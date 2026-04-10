from __future__ import annotations

import csv
import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple


def load_selection_ids(selection_file: Path) -> list[str]:
    if not selection_file.exists():
        raise FileNotFoundError(f"Arquivo de seleção não encontrado: {selection_file}")
    payload = json.loads(selection_file.read_text(encoding="utf-8"))
    return payload.get("selected_ids", [])


def filter_rows(rows: List[dict], args) -> List[dict]:
    selected_ids = set(load_selection_ids(Path(args.selection_file))) if args.selection_file else None
    out = []
    for row in rows:
        if selected_ids is not None and row["id_base"] not in selected_ids:
            continue
        if args.serie and row.get("serie") != args.serie:
            continue
        if args.autor and row.get("autor") != args.autor:
            continue
        if args.pasta and args.pasta.lower() not in (row.get("pasta_origem") or "").lower():
            continue
        if args.search:
            hay = " ".join([row.get("titulo", ""), row.get("slug_previsto", ""), row.get("serie", ""), row.get("autor", ""), row.get("pasta_origem", ""), row.get("id_base", "")]).lower()
            if args.search.lower() not in hay:
                continue
        if args.status_manifest and row.get("status_manifest") != args.status_manifest:
            continue
        if args.status_execucao and row.get("ultimo_status_execucao") != args.status_execucao:
            continue
        if args.only_published and not row.get("publicado"):
            continue
        if args.only_unpublished and row.get("publicado"):
            continue
        if args.only_changed and not row.get("alterado_desde_ultima_execucao"):
            continue
        if args.retry_failed and row.get("ultimo_status_execucao") != "ERROR":
            continue
        out.append(row)
    if args.limit:
        return out[: args.limit]
    return out


def default_runner_template(args) -> str:
    if not args.unit_script:
        return ""
    unit = str(Path(args.unit_script))
    if unit.lower().endswith(".py"):
        return (
            'python "{unit_script}" '
            '--titulo "{titulo}" '
            '--serie "{serie}" '
            '--resumo "{resumo}" '
            '--ordem {ordem} '
            '--visivel '
            '--html-a4 "{html_a4_path}" '
            '--html-a5 "{html_a5_path}" '
            '--html-tablet "{html_tablet_path}" '
            '--docx-a4 "{docx_a4_path}"'
        )
    return (
        'powershell -ExecutionPolicy Bypass -File "{unit_script}" '
        '--titulo "{titulo}" '
        '--serie "{serie}" '
        '--resumo "{resumo}" '
        '--ordem {ordem} '
        '--visivel '
        '--html-a4 "{html_a4_path}" '
        '--html-a5 "{html_a5_path}" '
        '--html-tablet "{html_tablet_path}" '
        '--docx-a4 "{docx_a4_path}"'
    )


def build_command(row: dict, args, ordem: int) -> str:
    template = args.runner_template or default_runner_template(args)
    if not template:
        raise ValueError("Modo de execução exige --runner-template ou --unit-script.")
    resumo = args.resumo_padrao or f"Sermão publicado em lote: {row.get('titulo', '')}".strip()
    mapping = {**row, "ordem": ordem, "resumo": resumo, "unit_script": args.unit_script or ""}
    return template.format(**mapping)


def execute_rows(rows: List[dict], args, log_path: Path, report_path: Path) -> Tuple[List[dict], dict]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = {"selected": len(rows), "ok_new": 0, "ok_updated": 0, "skip": 0, "error": 0}
    report_rows = []
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n=== EXECUÇÃO {now} ===\n")
        for idx, row in enumerate(rows, start=1):
            status = "DRY_RUN" if args.dry_run else "PENDENTE"
            msg = ""
            try:
                if row.get("status_manifest") != "COMPLETO":
                    status = "SKIP_INCOMPLETE"
                    msg = "Linha incompleta no manifest"
                    summary["skip"] += 1
                elif args.skip_if_exists and row.get("publicado"):
                    status = "SKIP_ALREADY_PUBLISHED"
                    msg = "Marcado como já publicado"
                    summary["skip"] += 1
                elif args.only_changed and not row.get("alterado_desde_ultima_execucao"):
                    status = "SKIP_UNCHANGED"
                    msg = "Sem alterações desde a última execução"
                    summary["skip"] += 1
                else:
                    cmd = build_command(row, args, ordem=idx)
                    log.write(f"[{idx}] {row['id_base']} -> {cmd}\n")
                    if args.dry_run:
                        status = "DRY_RUN"
                        msg = "Comando apenas exibido"
                    else:
                        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        if proc.returncode == 0:
                            status = "OK_UPDATED" if row.get("registro_existe") else "OK_NEW"
                            row["publicado"] = True
                            summary["ok_updated" if status == "OK_UPDATED" else "ok_new"] += 1
                            msg = (proc.stdout or "OK").strip()[:1200]
                        else:
                            status = "ERROR"
                            summary["error"] += 1
                            msg = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()[:2400]
                            if not args.continue_on_error:
                                raise RuntimeError(msg)
                row["ultimo_status_execucao"] = status
                row["mensagem_execucao"] = msg
                row["ultima_execucao_em"] = now
                report_rows.append({
                    "id_base": row.get("id_base"),
                    "titulo": row.get("titulo"),
                    "serie": row.get("serie"),
                    "status": status,
                    "mensagem": msg,
                })
                log.write(f"[{idx}] STATUS={status} MSG={msg[:400]}\n")
            except Exception as exc:  # noqa: BLE001
                row["ultimo_status_execucao"] = "ERROR"
                row["mensagem_execucao"] = str(exc)[:2400]
                row["ultima_execucao_em"] = now
                summary["error"] += 1
                report_rows.append({
                    "id_base": row.get("id_base"),
                    "titulo": row.get("titulo"),
                    "serie": row.get("serie"),
                    "status": "ERROR",
                    "mensagem": str(exc),
                })
                log.write(f"[{idx}] STATUS=ERROR MSG={exc}\n")
                if not args.continue_on_error:
                    break

    with report_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id_base", "titulo", "serie", "status", "mensagem"])
        writer.writeheader()
        writer.writerows(report_rows)
    return rows, summary
