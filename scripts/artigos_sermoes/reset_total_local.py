from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def repo_root_from_here() -> Path:
    cur = Path(__file__).resolve().parent
    for _ in range(10):
        if (cur / "manage.py").exists() or (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError("Raiz do projeto nao encontrada.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Reseta o ambiente local completo: BD de publicacao, workspace operacional, lotes de anexos "
            "e manifestos de trabalho, preservando Docs e arquivos de codex."
        )
    )
    parser.add_argument("--execute", action="store_true", help="Sem esta flag, apenas simula.")
    parser.add_argument(
        "--keep-taxonomy",
        action="store_true",
        help="Preserva Area e Autor ao delegar para reset_publicacao_local.py.",
    )
    parser.add_argument(
        "--keep-lotes",
        action="store_true",
        help="Preserva os lotes em Apenas_Local/anexos_filtrados e limpa apenas operacional/manifestos.",
    )
    return parser


def is_lote_dir(path: Path) -> bool:
    return path.is_dir() and bool(re.match(r"^\d{4}_\d{2}_\d{2}(?:-\d+|_\d+)?$", path.name))


def remove_path(path: Path, *, execute: bool) -> str:
    if not path.exists():
        return "NOT_FOUND"
    if not execute:
        return "DRY_DELETE"
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return "DELETED"


def backup_openai_artifacts(apenas_local: Path, stamp: str, *, execute: bool) -> tuple[Path, list[dict]]:
    backup_root = apenas_local / "backups" / "openai_artefatos" / stamp
    targets = [
        ("prompts_imagem", apenas_local / "operacional" / "artigos" / "prompts_imagem"),
        ("imagens_artigos", apenas_local / "operacional" / "artigos" / "imagens"),
        ("estudos_markdown", apenas_local / "operacional" / "dossies" / "markdown"),
        ("sermoes_markdown", apenas_local / "operacional" / "sermoes" / "markdown"),
    ]
    rows: list[dict] = []
    for label, src in targets:
        if not src.exists():
            rows.append({"kind": "backup_artifact", "target": str(src), "status": "NOT_FOUND", "detail": label})
            continue
        dst = backup_root / label
        if not execute:
            rows.append({"kind": "backup_artifact", "target": str(src), "status": "DRY_BACKUP", "detail": str(dst)})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        rows.append({"kind": "backup_artifact", "target": str(src), "status": "BACKED_UP", "detail": str(dst)})
    return backup_root, rows


def collect_homologacao_targets(homologacao_dir: Path) -> list[Path]:
    patterns = [
        "manifest_*.csv",
        "manifest_*.json",
        "manifest_*.html",
        "publicacao_sermoes_lote_*.log",
        "relatorio_lote_*.csv",
        "relatorio_lote_*.json",
    ]
    targets: list[Path] = []
    for pattern in patterns:
        targets.extend(sorted(homologacao_dir.glob(pattern)))
    unique: list[Path] = []
    seen: set[str] = set()
    for target in targets:
        key = str(target.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(target)
    return unique


def run_db_reset(root: Path, *, execute: bool, keep_taxonomy: bool) -> tuple[int, str]:
    script = root / "scripts" / "artigos_sermoes" / "reset_publicacao_local.py"
    cmd = [sys.executable, str(script)]
    if execute:
        cmd.append("--execute")
    if keep_taxonomy:
        cmd.append("--keep-taxonomy")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    return proc.returncode, output


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root_from_here()
    execute = bool(args.execute)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    apenas_local = root / "Apenas_Local"
    operacional_dir = apenas_local / "operacional"
    anexos_root = apenas_local / "anexos_filtrados"
    homologacao_dir = apenas_local / "scripts" / "homologacao"
    report_dir = homologacao_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / f"reset_total_local_{stamp}.csv"
    json_path = report_dir / f"reset_total_local_{stamp}.json"

    rows: list[dict] = []

    backup_root, backup_rows = backup_openai_artifacts(apenas_local, stamp, execute=execute)
    rows.extend(backup_rows)

    reset_rc, reset_output = run_db_reset(root, execute=execute, keep_taxonomy=bool(args.keep_taxonomy))
    rows.append(
        {
            "kind": "db_reset",
            "target": str(root / "scripts" / "artigos_sermoes" / "reset_publicacao_local.py"),
            "status": "OK" if reset_rc == 0 else f"ERROR({reset_rc})",
            "detail": reset_output[:4000],
        }
    )

    rows.append(
        {
            "kind": "workspace_dir",
            "target": str(operacional_dir),
            "status": remove_path(operacional_dir, execute=execute),
            "detail": "Limpeza integral do operacional",
        }
    )

    if not args.keep_lotes and anexos_root.exists():
        for child in sorted(anexos_root.iterdir(), key=lambda p: p.name):
            if child.name == "Docs":
                continue
            if not is_lote_dir(child):
                continue
            rows.append(
                {
                    "kind": "lote_dir",
                    "target": str(child),
                    "status": remove_path(child, execute=execute),
                    "detail": "Lote de anexos filtrados",
                }
            )

    for target in collect_homologacao_targets(homologacao_dir):
        rows.append(
            {
                "kind": "homologacao_artifact",
                "target": str(target),
                "status": remove_path(target, execute=execute),
                "detail": "Manifesto/log/relatorio operacional",
            }
        )

    post_checks = {
        "operacional_exists": operacional_dir.exists(),
        "lotes_restantes": sorted(
            str(p.name) for p in anexos_root.iterdir() if is_lote_dir(p)
        ) if anexos_root.exists() else [],
        "homologacao_artifacts_restantes": sorted(
            p.name for p in collect_homologacao_targets(homologacao_dir)
        ),
        "db_reset_rc": reset_rc,
        "backup_root": str(backup_root),
    }

    if execute:
        operacional_dir.mkdir(parents=True, exist_ok=True)

    verification = {
        "db_reset_ok": (reset_rc == 0),
        "operacional_ok": (operacional_dir.exists() if execute else True),
        "lotes_ok": (len(post_checks["lotes_restantes"]) == 0) if (execute and not args.keep_lotes) else True,
        "homologacao_ok": (len(post_checks["homologacao_artifacts_restantes"]) == 0) if execute else True,
    }
    verification["reset_total_ok"] = all(verification.values())

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["kind", "target", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "mode": "EXECUTE" if execute else "DRY-RUN",
        "keep_taxonomy": bool(args.keep_taxonomy),
        "keep_lotes": bool(args.keep_lotes),
        "verification": verification,
        "post_checks": post_checks,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] Modo              : {'EXECUTE' if execute else 'DRY-RUN'}")
    print(f"[OK] Reset BD         : {'OK' if reset_rc == 0 else f'ERRO({reset_rc})'}")
    print(f"[OK] Backup artefatos: {backup_root}")
    print(f"[OK] Operacional      : {'recriado vazio' if execute else 'seria limpo'}")
    print(f"[OK] Lotes restantes  : {len(post_checks['lotes_restantes'])}")
    print(f"[OK] Homologacao rest.: {len(post_checks['homologacao_artifacts_restantes'])}")
    print(f"[OK] Verificacao      : {'RESET_TOTAL_CONFIRMADO' if verification['reset_total_ok'] else 'RESET_TOTAL_INCONSISTENTE'}")
    print(f"[OK] Relatorio CSV    : {csv_path}")
    print(f"[OK] Relatorio JSON   : {json_path}")

    if reset_output:
        print()
        print("[INFO] Saida do reset do BD:")
        print(reset_output)

    return 0 if verification["reset_total_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
