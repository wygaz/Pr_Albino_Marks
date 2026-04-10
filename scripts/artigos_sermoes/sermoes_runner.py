from __future__ import annotations

import csv
import json
import re
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from artigos_operacional_utils import strip_editorial_prefixes
from pipeline_steps import parse_operation_spec


def load_selection_payload(selection_file: Path) -> dict:
    if not selection_file.exists():
        raise FileNotFoundError(f"Arquivo de seleÃ§Ã£o nÃ£o encontrado: {selection_file}")
    return json.loads(selection_file.read_text(encoding="utf-8-sig"))


def load_selection_ids(selection_file: Path) -> list[str]:
    return load_selection_payload(selection_file).get("selected_ids", [])


def resolve_execute_context(args) -> str:
    if getattr(args, "execute_context", ""):
        return args.execute_context
    if args.selection_file:
        payload = load_selection_payload(Path(args.selection_file))
        return str(payload.get("current_context") or "sermoes_formatados")
    return "sermoes_formatados"


def resolve_operation_plan(args):
    if getattr(args, "steps", ""):
        return parse_operation_spec(args.steps)
    if args.selection_file:
        payload = load_selection_payload(Path(args.selection_file))
        raw = ((payload.get("operation_plan") or {}).get("normalized") or payload.get("operation_spec") or "").strip()
        return parse_operation_spec(raw)
    return parse_operation_spec("")


def resolve_publish_kinds(args) -> str:
    if getattr(args, "publish_kinds", ""):
        return str(args.publish_kinds)
    if args.selection_file:
        payload = load_selection_payload(Path(args.selection_file))
        kinds = payload.get("publish_kinds")
        if isinstance(kinds, list):
            normalized = ",".join(str(k).strip() for k in kinds if str(k).strip())
            if normalized:
                return normalized
        kind = str(payload.get("publish_kind") or "").strip()
        if kind:
            return kind
    return "all"


def filter_rows(rows: List[dict], args) -> List[dict]:
    selected_ids = set(load_selection_ids(Path(args.selection_file))) if args.selection_file else None
    out = []
    for row in rows:
        if selected_ids is not None:
            row_ids = {
                str(row.get("id_base") or ""),
                f"artigo__{str(row.get('artigo_slug') or '').strip()}",
                f"artigo__{normalize_slug_like(str(row.get('titulo') or ''))}",
            }
            row_ids = {rid for rid in row_ids if rid and rid != "artigo__"}
            if not (row_ids & selected_ids):
                continue
        if args.serie and row.get("serie") != args.serie:
            continue
        if args.autor and row.get("autor") != args.autor:
            continue
        if args.pasta and args.pasta.lower() not in (row.get("pasta_origem") or "").lower():
            continue
        if args.search:
            hay = " ".join(
                [
                    row.get("titulo", ""),
                    row.get("slug_previsto", ""),
                    row.get("serie", ""),
                    row.get("autor", ""),
                    row.get("pasta_origem", ""),
                    row.get("id_base", ""),
                ]
            ).lower()
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


def normalize_slug_like(text: str) -> str:
    return ascii_slug(text)



def ascii_slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").strip().lower())
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "documento"


def run_shell_command(cmd: str | list[str], dry_run: bool) -> tuple[str, str]:
    commands = cmd if isinstance(cmd, list) else [cmd]
    if dry_run:
        return "DRY_RUN", "\n".join(commands)
    outputs: list[str] = []
    for current in commands:
        proc = subprocess.run(current, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        msg = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        if proc.returncode != 0:
            raise RuntimeError((msg or f"Falha ao executar: {current}")[:2400])
        if msg:
            outputs.append(msg)
    final = "\n".join(part for part in outputs if part).strip()
    return "OK", (final or "OK")[:2400]


def serie_dir_name(row: dict) -> str:
    serie = effective_series_value(row) or "Sem_Serie"
    return ascii_slug(serie) or "sem-serie"


def clean_workspace_stem(value: str) -> str:
    text = Path(value or "").stem
    text = re.sub(r"__dossie$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"__sermao$", "", text, flags=re.IGNORECASE)
    patterns = [
        r"__relatorio_tecnico__gpt-[^_]+",
        r"__relatorio_tecnico__.*?(?=__sermao__|$)",
        r"__sermao__gpt-[^_]+$",
        r"__sermao__.*$",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\d{1,3}__+", "", text)
    text = re.sub(r"^\d{1,3}_+", "", text)
    text = strip_editorial_prefixes(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" _-")


def md_slug_base_from_row(row: dict) -> str:
    candidates = [
        str(row.get("slug_previsto") or "").strip(),
        str(row.get("artigo_slug") or "").strip(),
        ascii_slug(str(row.get("titulo") or "")),
    ]
    for item in candidates:
        if item:
            return item
    docx = str(row.get("workspace_docx_path") or "")
    cleaned = clean_workspace_stem(docx)
    return ascii_slug(cleaned) or "documento"


def resolve_existing_path(directory: Path, preferred_name: str, legacy_patterns: list[str]) -> Path:
    preferred = directory / preferred_name
    if preferred.exists():
        return preferred
    for pattern in legacy_patterns:
        matches = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]
    return preferred


def effective_series_value(row: dict) -> str:
    serie = str(row.get("serie") or "").strip()
    if serie and ascii_slug(serie) not in {"series", "sem-serie"}:
        return serie
    pasta = str(row.get("pasta_origem") or row.get("serie_dir") or "").strip()
    match = re.match(r"^Serie_\d+__(.+)$", pasta)
    if match:
        return match.group(1).strip()
    base_name = Path(pasta).name.strip()
    if base_name and base_name.lower() not in {"sem-serie", "series"}:
        return base_name
    docx = str(row.get("workspace_docx_path") or "").strip()
    if docx:
        parent = Path(docx).parent.name
        match = re.match(r"^Serie_\d+__(.+)$", parent)
        if match:
            return match.group(1).strip()
        if parent and parent.lower() not in {"sem-serie", "series"}:
            return parent
    return ""


def relatorio_path_for(row: dict, args) -> Path:
    directory = Path(args.reports_root) / serie_dir_name(row)
    slug_base = md_slug_base_from_row(row)
    docx = Path(str(row.get("workspace_docx_path") or ""))
    legacy_stem = docx.stem
    return resolve_existing_path(
        directory,
        f"{slug_base}__dossie.md",
        [
            f"*{slug_base}__dossie.md",
            f"{legacy_stem}__relatorio_tecnico__{args.sermao_model}.md",
            f"{legacy_stem}__relatorio_tecnico__*.md",
            f"{slug_base}__relatorio_tecnico__*.md",
        ],
    )


def relatorio_html_path_for(row: dict, args) -> Path:
    root_dir = Path(args.dossies_formatados_root)
    directory = root_dir / serie_dir_name(row)
    slug_base = md_slug_base_from_row(row)
    docx = Path(str(row.get("workspace_docx_path") or ""))
    legacy_stem = docx.stem
    path = resolve_existing_path(
        directory,
        f"{slug_base}__dossie__a4.html",
        [
            f"*{slug_base}__dossie__a4.html",
            f"{legacy_stem}__dossie__a4.html",
            f"{legacy_stem}__relatorio_tecnico__*__a4.html",
            f"{slug_base}__relatorio_tecnico__*__a4.html",
        ],
    )
    if path.exists():
        return path
    return resolve_existing_path(
        root_dir,
        f"{slug_base}__dossie__a4.html",
        [
            f"*{slug_base}__dossie__a4.html",
            f"{legacy_stem}__dossie__a4.html",
            f"{legacy_stem}__relatorio_tecnico__*__a4.html",
            f"{slug_base}__relatorio_tecnico__*__a4.html",
        ],
    )


def sermao_html_path_for(row: dict, args, kind: str) -> Path:
    root_dir = Path(args.sermoes_formatados_root)
    directory = root_dir / serie_dir_name(row)
    slug_base = md_slug_base_from_row(row)
    docx = Path(str(row.get("workspace_docx_path") or ""))
    legacy_stem = docx.stem
    suffix = {
        "a4": "__sermao__a4.html",
        "a5": "__sermao__a5.html",
        "tablet": "__sermao__tablet.html",
    }[kind]
    path = resolve_existing_path(
        directory,
        f"{slug_base}{suffix}",
        [
            f"*{slug_base}{suffix}",
            f"{legacy_stem}{suffix}",
            f"{legacy_stem}__*.html",
        ],
    )
    if path.exists():
        return path
    return resolve_existing_path(
        root_dir,
        f"{slug_base}{suffix}",
        [
            f"*{slug_base}{suffix}",
            f"{legacy_stem}{suffix}",
            f"{legacy_stem}__*.html",
        ],
    )


def sermao_docx_path_for(row: dict, args) -> Path:
    root_dir = Path(args.sermoes_formatados_root)
    directory = root_dir / serie_dir_name(row)
    slug_base = md_slug_base_from_row(row)
    docx = Path(str(row.get("workspace_docx_path") or ""))
    legacy_stem = docx.stem
    path = resolve_existing_path(
        directory,
        f"{slug_base}__sermao__a4.docx",
        [
            f"*{slug_base}__sermao__a4.docx",
            f"{legacy_stem}__sermao__a4.docx",
            f"{legacy_stem}__*.docx",
        ],
    )
    if path.exists():
        return path
    return resolve_existing_path(
        root_dir,
        f"{slug_base}__sermao__a4.docx",
        [
            f"*{slug_base}__sermao__a4.docx",
            f"{legacy_stem}__sermao__a4.docx",
            f"{legacy_stem}__*.docx",
        ],
    )


def sermao_md_path_for(row: dict, args) -> Path:
    directory = Path(args.sermoes_md_root) / serie_dir_name(row)
    slug_base = md_slug_base_from_row(row)
    relatorio = relatorio_path_for(row, args)
    return resolve_existing_path(
        directory,
        f"{slug_base}__sermao.md",
        [
            f"*{slug_base}__sermao.md",
            f"{relatorio.stem}__sermao__{args.sermao_model}.md",
            f"{relatorio.stem}__sermao__*.md",
            f"{slug_base}__sermao__*.md",
        ],
    )


def should_skip_paid_generation(row: dict, args, plan_steps: list[int]) -> tuple[str, str]:
    if 10 in plan_steps or 11 in plan_steps:
        return "", ""
    if 7 in plan_steps:
        relatorio = relatorio_path_for(row, args)
        if relatorio.exists():
            return "SKIP_ALREADY_GENERATED", f"Dossie ja existe: {relatorio.name}"
    if 8 in plan_steps:
        sermao_md = sermao_md_path_for(row, args)
        if sermao_md.exists():
            return "SKIP_ALREADY_GENERATED", f"Sermao ja existe: {sermao_md.name}"
    return "", ""


def build_batch_step_command(step: int, args) -> str:
    python_exe = str(Path(args.python_exe))
    if step == 1:
        cmd = [
            python_exe,
            str(Path(args.extract_script)),
            "--lote",
            args.artigos_lote,
        ]
        if args.extract_ini:
            cmd.extend(["--ini", args.extract_ini])
        if args.extract_fim:
            cmd.extend(["--fim", args.extract_fim])
        if args.baixar_esbocos:
            cmd.append("--baixar-esbocos")
        if args.extract_ini_complementar and args.extract_fim_complementar:
            cmd.extend(
                [
                    "--ini-complementar",
                    args.extract_ini_complementar,
                    "--fim-complementar",
                    args.extract_fim_complementar,
                ]
            )
        return subprocess.list2cmdline(cmd)

    if step == 2:
        cmd = [
            python_exe,
            str(Path(args.prepare_script)),
            "organizar-lote",
            "--artigos-dir",
            str(Path(args.artigos_workspace_input)),
            "--esboco",
            str(Path(args.esboco_path)),
            "--saida",
            str(Path(args.operacional_output)),
        ]
        return subprocess.list2cmdline(cmd)

    if step == 3:
        cmd = [
            python_exe,
            str(Path(args.prompts_script)),
            "--series-root",
            str(Path(args.series_root)),
        ]
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        return subprocess.list2cmdline(cmd)

    if step == 4:
        cmd = [
            python_exe,
            str(Path(args.images_script)),
            "--run",
            "--prompts-csv",
            str(Path(args.prompts_csv)),
            "--out-root",
            str(Path(args.images_root)),
        ]
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        if args.overwrite_images:
            cmd.append("--overwrite")
        return subprocess.list2cmdline(cmd)

    if step == 5:
        cmd = [
            python_exe,
            str(Path(args.pdfs_script)),
            "--series-root",
            str(Path(args.series_root)),
            "--out-root",
            str(Path(args.pdfs_root)),
        ]
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        if args.overwrite_pdfs:
            cmd.append("--overwrite")
        return subprocess.list2cmdline(cmd)

    raise ValueError(f"Etapa batch sem comando: {step}")


def build_row_command(row: dict, args, ordem: int, plan_steps: list[int]) -> str:
    if 10 in plan_steps and row.get("html_a4_path"):
        if not row.get("html_a4_path"):
            raise ValueError("Linha sem HTML A4 para publicaÃ§Ã£o do sermÃ£o.")
        cmd = [
            str(Path(args.python_exe)),
            str(Path(args.publish_sermon_script)),
            "--titulo",
            str(row.get("titulo") or ""),
            "--serie",
            str(row.get("serie") or ""),
            "--resumo",
            str(args.resumo_padrao or f"SermÃ£o publicado em lote: {row.get('titulo', '')}".strip()),
            "--ordem",
            str(ordem),
            "--slug",
            str(row.get("slug_previsto") or row.get("slug_atual") or ""),
            "--html-a4",
            str(row.get("html_a4_path") or ""),
            "--html-a5",
            str(row.get("html_a5_path") or ""),
            "--html-tablet",
            str(row.get("html_tablet_path") or ""),
            "--docx-a4",
            str(row.get("docx_a4_path") or ""),
        ]
        return subprocess.list2cmdline(cmd)

    if 7 in plan_steps and 10 not in plan_steps:
        docx = row.get("workspace_docx_path")
        if not docx:
            raise ValueError("Linha sem DOCX de entrada para relatÃ³rio tÃ©cnico.")
        outdir = Path(args.reports_root) / serie_dir_name(row)
        cmd = [
            str(Path(args.python_exe)),
            str(Path(args.report_script)),
            "--docx",
            str(docx),
            "--outdir",
            str(outdir),
            "--model",
            str(args.sermao_model),
        ]
        return subprocess.list2cmdline(cmd)

    if 8 in plan_steps and 10 not in plan_steps:
        relatorio = relatorio_path_for(row, args)
        if not relatorio.exists():
            raise ValueError(f"RelatÃ³rio tÃ©cnico nÃ£o encontrado: {relatorio}")
        outdir = Path(args.sermoes_md_root) / serie_dir_name(row)
        cmd = [
            str(Path(args.python_exe)),
            str(Path(args.sermon_script)),
            "--relatorio",
            str(relatorio),
            "--outdir",
            str(outdir),
            "--model",
            str(args.sermao_model),
        ]
        return subprocess.list2cmdline(cmd)

    if 9 in plan_steps and 10 not in plan_steps:
        relatorio_md = relatorio_path_for(row, args)
        if not relatorio_md.exists():
            raise ValueError(f"Relatório técnico markdown não encontrado: {relatorio_md}")
        sermao_md = sermao_md_path_for(row, args)
        if not sermao_md.exists():
            raise ValueError(f"SermÃ£o markdown nÃ£o encontrado: {sermao_md}")
        relatorio_outdir = Path(args.dossies_formatados_root) / serie_dir_name(row)
        sermao_outdir = Path(args.sermoes_formatados_root) / serie_dir_name(row)
        relatorio_cmd = [
            str(Path(args.python_exe)),
            str(Path(args.report_export_script)),
            "--md",
            str(relatorio_md),
            "--outdir",
            str(relatorio_outdir),
        ]
        sermao_cmd = [
            str(Path(args.python_exe)),
            str(Path(args.export_script)),
            "--md",
            str(sermao_md),
            "--outdir",
            str(sermao_outdir),
        ]
        return [subprocess.list2cmdline(relatorio_cmd), subprocess.list2cmdline(sermao_cmd)]

    if 6 in plan_steps and 10 not in plan_steps:
        docx = row.get("workspace_docx_path")
        if not docx:
            raise ValueError("Linha sem DOCX de entrada para publicaÃ§Ã£o do artigo.")
        cmd = [
            str(Path(args.python_exe)),
            str(Path(args.publish_articles_script)),
            "--docx-path",
            str(docx),
            "--series-root",
            str(Path(args.series_root)),
            "--pdf-root",
            str(Path(args.pdfs_root)),
            "--img-root",
            str(Path(args.images_root)),
            "--django-settings",
            str(args.django_settings or "pralbinomarks.settings"),
            "--publish-kinds",
            resolve_publish_kinds(args),
        ]
        if args.overwrite_media:
            cmd.append("--overwrite-media")
        if args.dry_run:
            cmd.append("--dry-run")
        return subprocess.list2cmdline(cmd)

    if 10 in plan_steps:
        docx = row.get("workspace_docx_path") or row.get("docx_a4_path")
        if not docx:
            raise ValueError("Linha sem DOCX de entrada para pipeline completo.")
        dossie_formatados = Path(args.dossies_formatados_root) / serie_dir_name(row)
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(Path(args.pipeline_script)),
            "-Docx",
            str(docx),
            "-Serie",
            str(row.get("serie") or ""),
            "-Titulo",
            str(row.get("titulo") or ""),
            "-Resumo",
            str(args.resumo_padrao or f"SermÃ£o publicado em lote: {row.get('titulo', '')}".strip()),
            "-Ordem",
            str(ordem),
            "-RelatoriosOutDir",
            str(Path(args.reports_root) / serie_dir_name(row)),
            "-DossiesFormatadosOutDir",
            str(dossie_formatados),
            "-SermoesOutDir",
            str(Path(args.sermoes_md_root) / serie_dir_name(row)),
            "-FormatadosOutDir",
            str(Path(args.sermoes_formatados_root) / serie_dir_name(row)),
        ]
        return subprocess.list2cmdline(cmd)

    raise ValueError("Etapas nÃ£o ligadas para este contexto/combinaÃ§Ã£o.")


def build_row_command_v2(row: dict, args, ordem: int, plan_steps: list[int]) -> str:
    serie_value = effective_series_value(row)

    if 10 in plan_steps and row.get("html_a4_path"):
        relatorio_html = relatorio_html_path_for(row, args)
        cmd = [
            str(Path(args.python_exe)),
            str(Path(args.publish_sermon_script)),
            "--titulo",
            str(row.get("titulo") or ""),
            "--serie",
            serie_value,
            "--resumo",
            str(args.resumo_padrao or f"SermÃ£o publicado em lote: {row.get('titulo', '')}".strip()),
            "--ordem",
            str(ordem),
            "--slug",
            str(row.get("slug_previsto") or row.get("slug_atual") or ""),
            "--html-a4",
            str(row.get("html_a4_path") or ""),
            "--html-a5",
            str(row.get("html_a5_path") or ""),
            "--html-tablet",
            str(row.get("html_tablet_path") or ""),
            "--docx-a4",
            str(row.get("docx_a4_path") or ""),
            "--relatorio-html",
            str(row.get("relatorio_html_path") or relatorio_html),
        ]
        return subprocess.list2cmdline(cmd)

    if 11 in plan_steps:
        html_a4 = Path(str(row.get("html_a4_path") or sermao_html_path_for(row, args, "a4")))
        html_a5 = Path(str(row.get("html_a5_path") or sermao_html_path_for(row, args, "a5")))
        html_tablet = Path(str(row.get("html_tablet_path") or sermao_html_path_for(row, args, "tablet")))
        docx_a4 = Path(str(row.get("docx_a4_path") or sermao_docx_path_for(row, args)))
        relatorio_html = Path(str(row.get("relatorio_html_path") or relatorio_html_path_for(row, args)))
        for path_obj, label in [
            (html_a4, "HTML A4 do sermao"),
            (html_a5, "HTML A5 do sermao"),
            (html_tablet, "HTML Tablet do sermao"),
            (docx_a4, "DOCX A4 do sermao"),
            (relatorio_html, "HTML do dossie"),
        ]:
            if not path_obj.exists():
                raise ValueError(f"{label} nao encontrado: {path_obj}")
        cmd = [
            str(Path(args.python_exe)),
            str(Path(args.publish_sermon_script)),
            "--titulo",
            str(row.get("titulo") or ""),
            "--serie",
            effective_series_value(row),
            "--resumo",
            str(args.resumo_padrao or f"SermÃƒÂ£o publicado em lote: {row.get('titulo', '')}".strip()),
            "--ordem",
            str(ordem),
            "--slug",
            str(row.get("slug_previsto") or row.get("artigo_slug") or row.get("slug_atual") or ""),
            "--html-a4",
            str(html_a4),
            "--html-a5",
            str(html_a5),
            "--html-tablet",
            str(html_tablet),
            "--docx-a4",
            str(docx_a4),
            "--relatorio-html",
            str(relatorio_html),
        ]
        return subprocess.list2cmdline(cmd)

    if 7 in plan_steps and 10 not in plan_steps:
        docx = row.get("workspace_docx_path")
        if not docx:
            raise ValueError("Linha sem DOCX de entrada para relatÃ³rio tÃ©cnico.")
        outdir = Path(args.reports_root) / serie_dir_name(row)
        cmd = [
            str(Path(args.python_exe)),
            str(Path(args.report_script)),
            "--docx",
            str(docx),
            "--outdir",
            str(outdir),
            "--model",
            str(args.sermao_model),
        ]
        return subprocess.list2cmdline(cmd)

    if 8 in plan_steps and 10 not in plan_steps:
        relatorio = relatorio_path_for(row, args)
        if not relatorio.exists():
            raise ValueError(f"RelatÃ³rio tÃ©cnico nÃ£o encontrado: {relatorio}")
        outdir = Path(args.sermoes_md_root) / serie_dir_name(row)
        cmd = [
            str(Path(args.python_exe)),
            str(Path(args.sermon_script)),
            "--relatorio",
            str(relatorio),
            "--outdir",
            str(outdir),
            "--model",
            str(args.sermao_model),
        ]
        return subprocess.list2cmdline(cmd)

    if 9 in plan_steps and 10 not in plan_steps:
        relatorio_md = relatorio_path_for(row, args)
        if not relatorio_md.exists():
            raise ValueError(f"Relatório técnico markdown não encontrado: {relatorio_md}")
        sermao_md = sermao_md_path_for(row, args)
        if not sermao_md.exists():
            raise ValueError(f"SermÃ£o markdown nÃ£o encontrado: {sermao_md}")
        relatorio_outdir = Path(args.dossies_formatados_root) / serie_dir_name(row)
        sermao_outdir = Path(args.sermoes_formatados_root) / serie_dir_name(row)
        relatorio_cmd = [
            str(Path(args.python_exe)),
            str(Path(args.report_export_script)),
            "--md",
            str(relatorio_md),
            "--outdir",
            str(relatorio_outdir),
        ]
        sermao_cmd = [
            str(Path(args.python_exe)),
            str(Path(args.export_script)),
            "--md",
            str(sermao_md),
            "--outdir",
            str(sermao_outdir),
        ]
        return [subprocess.list2cmdline(relatorio_cmd), subprocess.list2cmdline(sermao_cmd)]

    if 6 in plan_steps and 10 not in plan_steps:
        docx = row.get("workspace_docx_path")
        if not docx:
            raise ValueError("Linha sem DOCX de entrada para publicaÃ§Ã£o do artigo.")
        cmd = [
            str(Path(args.python_exe)),
            str(Path(args.publish_articles_script)),
            "--docx-path",
            str(docx),
            "--series-root",
            str(Path(args.series_root)),
            "--pdf-root",
            str(Path(args.pdfs_root)),
            "--img-root",
            str(Path(args.images_root)),
            "--django-settings",
            str(args.django_settings or "pralbinomarks.settings"),
            "--publish-kinds",
            resolve_publish_kinds(args),
        ]
        if args.overwrite_media:
            cmd.append("--overwrite-media")
        if args.dry_run:
            cmd.append("--dry-run")
        return subprocess.list2cmdline(cmd)

    if 10 in plan_steps:
        docx = row.get("workspace_docx_path") or row.get("docx_a4_path")
        if not docx:
            raise ValueError("Linha sem DOCX de entrada para pipeline completo.")
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(Path(args.pipeline_script)),
            "-Docx",
            str(docx),
            "-Serie",
            serie_value,
            "-Titulo",
            str(row.get("titulo") or ""),
            "-Slug",
            str(row.get("slug_previsto") or row.get("artigo_slug") or row.get("slug_atual") or ""),
            "-Resumo",
            str(args.resumo_padrao or f"SermÃ£o publicado em lote: {row.get('titulo', '')}".strip()),
            "-Ordem",
            str(ordem),
        ]
        return subprocess.list2cmdline(cmd)

    raise ValueError("Etapas nÃ£o ligadas para este contexto/combinaÃ§Ã£o.")


def execute_rows(rows: List[dict], args, log_path: Path, report_path: Path) -> Tuple[List[dict], dict]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context = resolve_execute_context(args)
    plan = resolve_operation_plan(args)
    summary = {"selected": len(rows), "ok_new": 0, "ok_updated": 0, "skip": 0, "error": 0, "batch_ok": 0}
    report_rows = []

    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n=== EXECUÃ‡ÃƒO {now} CONTEXTO={context} STEPS={plan.normalized or '-'} ===\n")

        if context == "artigos_sem_sermao" and any(step in plan.steps for step in [1, 2, 3, 4, 5]):
            for step in [1, 2, 3, 4, 5]:
                if step not in plan.steps:
                    continue
                try:
                    cmd = build_batch_step_command(step, args)
                    log.write(f"[BATCH:{step}] {cmd}\n")
                    status, msg = run_shell_command(cmd, args.dry_run)
                    summary["batch_ok"] += 1
                    report_rows.append(
                        {
                            "id_base": f"batch_step_{step}",
                            "titulo": f"Batch step {step}",
                            "serie": "",
                            "status": status,
                            "mensagem": msg,
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    summary["error"] += 1
                    report_rows.append(
                        {
                            "id_base": f"batch_step_{step}",
                            "titulo": f"Batch step {step}",
                            "serie": "",
                            "status": "ERROR",
                            "mensagem": str(exc),
                        }
                    )
                    log.write(f"[BATCH:{step}] STATUS=ERROR MSG={exc}\n")
                    if not args.continue_on_error:
                        with report_path.open("w", encoding="utf-8", newline="") as f:
                            writer = csv.DictWriter(f, fieldnames=["id_base", "titulo", "serie", "status", "mensagem"])
                            writer.writeheader()
                            writer.writerows(report_rows)
                        return rows, summary

        for idx, row in enumerate(rows, start=1):
            try:
                if context == "artigos_sem_sermao":
                    skip_status, skip_msg = should_skip_paid_generation(row, args, plan.steps)
                    if skip_status:
                        status = skip_status
                        msg = skip_msg
                        summary["skip"] += 1
                        row["ultimo_status_execucao"] = status
                        row["mensagem_execucao"] = msg
                        row["ultima_execucao_em"] = now
                        report_rows.append(
                            {
                                "id_base": row.get("id_base"),
                                "titulo": row.get("titulo"),
                                "serie": row.get("serie"),
                                "status": status,
                                "mensagem": msg,
                            }
                        )
                        log.write(f"[{idx}] STATUS={status} MSG={msg[:400]}\n")
                        continue
                if context == "sermoes_formatados" and row.get("status_manifest") != "COMPLETO":
                    status = "SKIP_INCOMPLETE"
                    msg = "Linha incompleta no manifest"
                    summary["skip"] += 1
                elif args.skip_if_exists and row.get("publicado"):
                    status = "SKIP_ALREADY_PUBLISHED"
                    msg = "Marcado como jÃ¡ publicado"
                    summary["skip"] += 1
                elif args.only_changed and not row.get("alterado_desde_ultima_execucao"):
                    status = "SKIP_UNCHANGED"
                    msg = "Sem alteraÃ§Ãµes desde a Ãºltima execuÃ§Ã£o"
                    summary["skip"] += 1
                elif context == "artigos_sem_sermao" and set(plan.steps).issubset({1, 2, 3, 4, 5}):
                    status = "BATCH_ONLY"
                    msg = "Itens preservados; execuÃ§Ã£o ocorreu apenas nos passos batch"
                else:
                    cmd = build_row_command_v2(row, args, idx, plan.steps)
                    print(f"[INFO] Executando {idx}/{len(rows)}: {row.get('titulo') or row.get('id_base')} | steps={plan.normalized or '-'}")
                    if isinstance(cmd, list):
                        for part in cmd:
                            log.write(f"[{idx}] {row['id_base']} -> {part}\n")
                    else:
                        log.write(f"[{idx}] {row['id_base']} -> {cmd}\n")
                    status, msg = run_shell_command(cmd, args.dry_run)
                    status = "OK_UPDATED" if row.get("registro_existe") else "OK_NEW"
                    row["publicado"] = True
                    row["registro_existe"] = True
                    summary["ok_updated" if status == "OK_UPDATED" else "ok_new"] += 1

                row["ultimo_status_execucao"] = status
                row["mensagem_execucao"] = msg
                row["ultima_execucao_em"] = now
                report_rows.append(
                    {
                        "id_base": row.get("id_base"),
                        "titulo": row.get("titulo"),
                        "serie": row.get("serie"),
                        "status": status,
                        "mensagem": msg,
                    }
                )
                log.write(f"[{idx}] STATUS={status} MSG={msg[:400]}\n")
            except Exception as exc:  # noqa: BLE001
                row["ultimo_status_execucao"] = "ERROR"
                row["mensagem_execucao"] = str(exc)[:2400]
                row["ultima_execucao_em"] = now
                summary["error"] += 1
                report_rows.append(
                    {
                        "id_base": row.get("id_base"),
                        "titulo": row.get("titulo"),
                        "serie": row.get("serie"),
                        "status": "ERROR",
                        "mensagem": str(exc),
                    }
                )
                log.write(f"[{idx}] STATUS=ERROR MSG={exc}\n")
                if not args.continue_on_error:
                    break

    with report_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id_base", "titulo", "serie", "status", "mensagem"])
        writer.writeheader()
        writer.writerows(report_rows)
    return rows, summary
