from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from artigos_operacional_utils import docx_internal_title, strip_editorial_prefixes
from pipeline_steps import parse_operation_spec
from sermoes_django import normalize_lookup, setup_django

ARTICLE_EXTS = {".docx", ".html", ".htm", ".pdf", ".md", ".txt"}
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")

ARTICLE_ALIASES = {
    "origem-do-grande-conflito-cosmico-de-conceitos-espirituais": "a-origem-do-grande-conflito-de-conceitos-espirituais",
    "o-principio-biblico-do-simbolismo": "o-principio-do-simbolismo",
    "a-reconquista-do-dominio-perdido": "a-reconquista-do-dominio",
    "a-quinta-trombeta-e-o-selo-de-deus": "a-quinta-praga-e-o-selo-de-deus",
    "setima-trombeta-e-a-setima-praga": "setima-trombeta-e-setima-praga",
    "a-quem-simboliza-a-besta-nao-qualificada": "quem-e-a-besta-nao-qualificada",
    "a-besta-que-era-e-agora-nao-e-e-o-oitavo-rei": "a-besta-que-era-nao-e-e-o-oitavo-rei",
    "a-torah-nomos-lei-mandamentos-ordenancas-e-graca": "a-lei-torah-nomos-mandamentos-ordenancas-e-a-graca",
    "o-novo-testamento-jesus-a-lei-e-os-profetas": "o-novo-testamento-jesus-e-a-lei",
    "ninguem-e-justificado-por-obras-da-lei": "ninguem-e-justificado-pelas-obras-da-lei",
    "paulo-e-a-graca-de-deus": "o-apostolo-paulo-e-a-graca-de-deus",
    "maldicao-da-lei": "a-maldicao-da-lei",
    "a-lei-moral-e-as-aliancas-de-deus": "a-lei-moral-e-as-aliancas",
    "a-lei-nao-revoga-a-alianca": "a-lei-nao-anula-as-aliancas",
    "a-lei-acrescentada-por-causa-das-transgressoes": "por-causa-das-transgressoes",
    "o-conflito-cosmico-e-os-dois-poderes-em-confronto": "o-conflito-e-os-dois-poderes-em-confronto",
    "os-mil-duzentos-e-sessenta-anos-e-satanas": "os-mil-duzentos-sessenta-anos-e-satanas",
    "a-divisao-da-historia-da-humanidade-predita": "a-divisao-da-historia-da-humanidade-predita",
}
REVERSE_ARTICLE_ALIASES = {value: key for key, value in ARTICLE_ALIASES.items()}


def _sanitize_display_title(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^\d{8}_\d{6}__", "", text)
    text = re.sub(r"^\d{2}__", "", text)
    text = re.sub(r"^\d+\s*(?:[-_. ]+\s*)?", "", text)
    text = re.sub(r"^(?:[A-Za-z]{1,5}\d{2,6}\s+)+", "", text)
    text = strip_editorial_prefixes(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _covered_sets(sermon_rows: list[dict]) -> tuple[set[str], set[str], set[str]]:
    ids: set[str] = set()
    slugs: set[str] = set()
    titles: set[str] = set()
    for row in sermon_rows:
        for value in [row.get("artigo_id"), row.get("sermao_id")]:
            value = str(value or "").strip()
            if value:
                ids.add(value)
        for value in [row.get("artigo_slug"), row.get("slug_previsto")]:
            value = str(value or "").strip()
            if value:
                slugs.add(value)
        for value in [row.get("titulo"), row.get("rotulo_curto"), row.get("artigo_titulo")]:
            key = normalize_lookup(str(value or ""))
            if key:
                titles.add(key)
    return ids, slugs, titles


def _alias_slug(value: str) -> str:
    slug = str(value or "").strip()
    if not slug:
        return ""
    return ARTICLE_ALIASES.get(slug, slug)


def _candidate_slug_keys(value: str) -> list[str]:
    slug = str(value or "").strip()
    if not slug:
        return []
    candidates = [slug]
    canonical = ARTICLE_ALIASES.get(slug, "")
    legacy = REVERSE_ARTICLE_ALIASES.get(slug, "")
    for item in [canonical, legacy]:
        if item and item not in candidates:
            candidates.append(item)
    return candidates


def _clean_workspace_stem(path: Path) -> str:
    stem = path.stem
    for suffix in ["__A4", "__A5", "__tablet", "_A4", "_A5", "_tablet", "__a4", "__a5"]:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    stem = re.sub(r"^\d{1,3}__+", "", stem)
    stem = re.sub(r"^\d{1,3}_+", "", stem)
    stem = strip_editorial_prefixes(stem)
    return stem.strip(" _-")


def _workspace_display_title(workspace: dict[str, Any] | None) -> str:
    if not workspace:
        return ""
    docx_path = str(workspace.get("docx_path") or "").strip()
    if docx_path:
        title = _sanitize_display_title(docx_internal_title(Path(docx_path)))
        if title:
            return title
    return _sanitize_display_title(str(workspace.get("display_name", "") or "").strip())


def _prompts_csv(root: Path) -> Path:
    return root / "Apenas_Local" / "operacional" / "artigos" / "prompts_imagem" / "prompts_imagens_operacional.csv"


def _guess_image_for_docx(root: Path, docx_path: str) -> str:
    if not docx_path:
        return ""
    docx = Path(docx_path)
    try:
        series_root = root / "Apenas_Local" / "operacional" / "artigos" / "series"
        rel = docx.relative_to(series_root)
    except Exception:
        return ""
    image_dir = root / "Apenas_Local" / "operacional" / "artigos" / "imagens" / rel.parent
    stems = []
    raw_stem = docx.stem
    clean_stem = _clean_workspace_stem(docx)
    for item in [raw_stem, clean_stem, _alias_slug(clean_stem)]:
        item = str(item or "").strip()
        if item and item not in stems:
            stems.append(item)
    for stem in stems:
        for ext in IMAGE_EXTS:
            candidate = image_dir / f"{stem}{ext}"
            if candidate.exists():
                return str(candidate)
    return ""


def _field_exists(field: Any) -> bool:
    try:
        name = str(getattr(field, "name", "") or "").strip()
        if not name:
            return False
        storage = getattr(field, "storage", None)
        if storage is None:
            return True
        try:
            return bool(storage.exists(name))
        except Exception:
            return True
    except Exception:
        return False


def _published_kinds(artigo: Any | None) -> tuple[bool, bool, bool]:
    if artigo is None:
        return False, False, False
    return (
        _field_exists(getattr(artigo, "arquivo_word", None)),
        _field_exists(getattr(artigo, "arquivo_pdf", None)),
        _field_exists(getattr(artigo, "imagem_capa", None)),
    )


def _recommended_publish_kind(pub_docx: bool, pub_pdf: bool, pub_img: bool) -> str:
    missing = []
    if not pub_docx:
        missing.append("docx")
    if not pub_pdf:
        missing.append("pdf")
    if not pub_img:
        missing.append("img")
    if not missing:
        return ""
    if len(missing) == 1:
        return missing[0]
    return "all"


def scan_article_workspace(root: Path, input_dir: Path | None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    info: dict[str, Any] = {"enabled": False, "base_dir": "", "files": 0, "groups": 0, "warnings": []}
    if not input_dir:
        return {}, info
    input_dir = Path(input_dir)
    if not input_dir.exists():
        info["warnings"].append(f"InputDirArtigos não encontrado: {input_dir}")
        return {}, info

    info["enabled"] = True
    info["base_dir"] = str(input_dir)
    groups: dict[str, dict[str, Any]] = {}
    serie_dirs = sorted([p for p in input_dir.glob("Serie_*") if p.is_dir()])
    roots = serie_dirs or [input_dir]
    if serie_dirs:
        info["base_dir"] = ", ".join(str(p) for p in serie_dirs)

    for root_dir in roots:
        for path in root_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in ARTICLE_EXTS:
                continue
            info["files"] += 1
            raw_stem = _clean_workspace_stem(path)
            key = normalize_lookup(raw_stem)
            if not key:
                continue
            rel = path.relative_to(input_dir).as_posix()
            entry = groups.setdefault(
                key,
                {
                    "lookup_key": key,
                    "display_name": raw_stem,
                    "paths": [],
                    "paths_rel": [],
                    "docx_path": "",
                    "html_path": "",
                    "pdf_path": "",
                    "image_path": "",
                    "source_types": set(),
                },
            )
            entry["paths"].append(str(path))
            entry["paths_rel"].append(rel)
            suffix = path.suffix.lower()
            if suffix == ".docx" and not entry["docx_path"]:
                entry["docx_path"] = str(path)
            elif suffix in {".html", ".htm"} and not entry["html_path"]:
                entry["html_path"] = str(path)
            elif suffix == ".pdf" and not entry["pdf_path"]:
                entry["pdf_path"] = str(path)
            entry["source_types"].add(suffix.lstrip("."))

    for entry in groups.values():
        entry["image_path"] = _guess_image_for_docx(root, entry.get("docx_path", ""))

    info["groups"] = len(groups)
    return groups, info


def _workspace_for_article(artigo: Any, groups: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    candidates = []
    for value in [getattr(artigo, "slug", ""), getattr(artigo, "titulo", "")]:
        key = normalize_lookup(str(value or ""))
        if key:
            candidates.append(key)
    for key in candidates:
        for alt in _candidate_slug_keys(key):
            if alt in groups:
                return groups[alt]
    return None


def _infer_completed_steps(workspace: dict[str, Any] | None, artigo: Any | None, root: Path) -> list[int]:
    steps: set[int] = set()
    if workspace and workspace.get("docx_path"):
        steps.update({1, 2})
    if _prompts_csv(root).exists():
        steps.add(3)
    if workspace and workspace.get("image_path"):
        steps.add(4)
    if workspace and workspace.get("pdf_path"):
        steps.add(5)
    if artigo is not None and getattr(artigo, "pk", None):
        if getattr(artigo, "arquivo_word", None) or getattr(artigo, "arquivo_pdf", None) or getattr(artigo, "imagem_capa", None):
            steps.add(6)
    return sorted(steps)


def _steps_as_text(steps: list[int]) -> str:
    return ",".join(str(s) for s in steps)


def _stage_from_workspace(workspace: dict[str, Any] | None, artigo: Any | None, root: Path) -> tuple[str, list[int], str, list[int], str]:
    completed = _infer_completed_steps(workspace, artigo, root)
    completed_text = _steps_as_text(completed)
    pub_docx, pub_pdf, pub_img = _published_kinds(artigo)
    if pub_docx and pub_pdf and pub_img:
        plan = parse_operation_spec("")
        return "PUBLICADO_ARTIGO", plan.steps, plan.normalized, completed, completed_text
    if workspace and workspace.get("pdf_path"):
        plan = parse_operation_spec("6")
        return "PDF_LOCALIZADO", plan.steps, plan.normalized, completed, completed_text
    if workspace and workspace.get("image_path"):
        plan = parse_operation_spec("5-6")
        return "IMAGEM_LOCALIZADA", plan.steps, plan.normalized, completed, completed_text
    if 3 in completed:
        plan = parse_operation_spec("4-6")
        return "PROMPT_LOCALIZADO", plan.steps, plan.normalized, completed, completed_text
    if workspace and workspace.get("docx_path"):
        plan = parse_operation_spec("3-6")
        return "DOCX_LOCALIZADO", plan.steps, plan.normalized, completed, completed_text
    plan = parse_operation_spec("1-6")
    return "SEM_INSUMOS_LOCAIS", plan.steps, plan.normalized, completed, completed_text


def build_article_pending_row(artigo: Any | None, workspace: dict[str, Any] | None, root: Path, input_dir_artigos: Path | None = None) -> dict[str, Any]:
    titulo_workspace = _workspace_display_title(workspace).strip()
    titulo_bd = str(getattr(artigo, "titulo", "") or "").strip() if artigo is not None else ""
    titulo = (titulo_workspace or titulo_bd).strip()
    slug = (str(getattr(artigo, "slug", "") or "") if artigo is not None else normalize_lookup(titulo).replace("_", "-")).strip()
    area_obj = getattr(artigo, "area", None) if artigo is not None else None
    autor_obj = getattr(artigo, "autor", None) if artigo is not None else None
    serie = str(getattr(area_obj, "nome", "") or "").strip()
    autor = str(getattr(autor_obj, "nome", "") or "").strip()
    etapa_atual, operacao_steps, operacao_spec, etapas_concluidas, etapas_concluidas_texto = _stage_from_workspace(workspace, artigo, root)
    source_types = ", ".join(sorted((workspace or {}).get("source_types", [])))
    rel_paths = ", ".join((workspace or {}).get("paths_rel", [])[:3])
    lookup_key = normalize_lookup(slug or titulo)
    publicado_docx, publicado_pdf, publicado_img = _published_kinds(artigo)
    publicado = publicado_docx and publicado_pdf and publicado_img
    publish_kind_recomendado = _recommended_publish_kind(publicado_docx, publicado_pdf, publicado_img)
    return {
        "context": "artigos_sem_sermao",
        "id_base": f"artigo__{getattr(artigo, 'id', lookup_key or 'arquivo')}",
        "titulo": titulo,
        "rotulo_curto": titulo,
        "slug_previsto": slug,
        "serie": serie,
        "autor": autor,
        "pasta_origem": str(input_dir_artigos or ""),
        "pasta_relativa": rel_paths,
        "destino_media_rel": f"media/artigos/{slug}" if slug else "",
        "nome_arquivo_canonico": f"{slug}.docx" if slug else "",
        "fonte_titulo": (
            "workspace:docx"
            if titulo_workspace
            else ("bd:titulo" if artigo is not None else "workspace:arquivo")
        ),
        "fonte_serie": "bd:area" if serie else "",
        "fonte_autor": "bd:autor" if autor else "",
        "artigo_id": str(getattr(artigo, "id", "") or ""),
        "artigo_slug": slug,
        "artigo_titulo": titulo_bd or titulo,
        "artigo_visivel": bool(getattr(artigo, "visivel", False)) if artigo is not None else False,
        "bd_match_kind": "artigo_pendente" if artigo is not None else "workspace_sem_bd",
        "workspace_docx_path": (workspace or {}).get("docx_path", ""),
        "workspace_html_path": (workspace or {}).get("html_path", ""),
        "workspace_pdf_path": (workspace or {}).get("pdf_path", ""),
        "workspace_image_path": (workspace or {}).get("image_path", ""),
        "workspace_source_types": source_types,
        "workspace_lookup_key": lookup_key,
        "publicado_docx": publicado_docx,
        "publicado_pdf": publicado_pdf,
        "publicado_img": publicado_img,
        "publish_kind_recomendado": publish_kind_recomendado,
        "html_a4_path": "",
        "html_a5_path": "",
        "html_tablet_path": "",
        "docx_a4_path": "",
        "pdf_a4_path": "",
        "pdf_a5_path": "",
        "pdf_tablet_path": "",
        "html_a4_ok": False,
        "html_a5_ok": False,
        "html_tablet_ok": False,
        "docx_a4_ok": bool((workspace or {}).get("docx_path")),
        "pdf_a4_ok": bool((workspace or {}).get("pdf_path")),
        "pdf_a5_ok": False,
        "pdf_tablet_ok": False,
        "completo_ok": False,
        "status_manifest": "PUBLICADO_ARTIGO" if publicado else "PENDENTE_PUBLICACAO_ARTIGO",
        "duplicado_detectado": False,
        "registro_existe": artigo is not None and bool(getattr(artigo, "pk", None)),
        "publicado": publicado,
        "sermao_id": "",
        "slug_atual": slug,
        "ultimo_status_execucao": "PUBLICADO" if publicado else "PENDENTE_GERACAO",
        "ultima_execucao_em": "",
        "mensagem_execucao": "",
        "assinatura_entrada": "",
        "alterado_desde_ultima_execucao": False,
        "criado_em": "",
        "atualizado_em": "",
        "origem_scan": "bd:Artigo" if artigo is not None else "workspace:artigo",
        "etapa_atual": etapa_atual,
        "operacao_recomendada": operacao_spec,
        "operacao_steps": operacao_steps,
        "etapas_concluidas_inferidas": etapas_concluidas,
        "etapas_concluidas_texto": etapas_concluidas_texto,
        "ultima_operacao_solicitada": "",
        "historico_operacoes": "",
        "observacoes": (
            f"Pendência pronta para geração/publicação em lote. Fontes locais: {source_types or 'nenhuma'}. "
            f"Etapas concluídas (inferidas): {etapas_concluidas_texto or 'nenhuma'}. "
            f"Publicação BD: docx={'sim' if publicado_docx else 'não'}, pdf={'sim' if publicado_pdf else 'não'}, img={'sim' if publicado_img else 'não'}. "
            f"Execute operações {operacao_spec or '1-6'} conforme necessário."
        ),
    }


def fetch_articles_without_sermon(
    root: Path,
    settings_module: str | None,
    sermon_rows: list[dict],
    input_dir_artigos: Path | None = None,
    workspace_artigos: Path | None = None,
) -> tuple[list[dict], dict[str, Any]]:
    info: dict[str, Any] = {
        "enabled": False,
        "settings_module": "",
        "total_artigos": 0,
        "pending": 0,
        "warnings": [],
        "workspace_enabled": False,
        "workspace_groups": 0,
    }

    workspace_base = workspace_artigos or input_dir_artigos
    workspace_groups, workspace_info = scan_article_workspace(root, workspace_base)
    info["workspace_enabled"] = workspace_info.get("enabled", False)
    info["workspace_groups"] = workspace_info.get("groups", 0)
    info["warnings"].extend(workspace_info.get("warnings", []))
    info["total_artigos"] = int(workspace_info.get("groups", 0) or 0)

    try:
        module = setup_django(root, settings_module)
        info["enabled"] = True
        info["settings_module"] = module
    except Exception as exc:  # noqa: BLE001
        info["warnings"].append(f"BD indisponível para artigos: {exc}")
        pending_rows = [
            build_article_pending_row(None, ws, root=root, input_dir_artigos=input_dir_artigos)
            for ws in workspace_groups.values()
        ]
        info["pending"] = len(pending_rows)
        return pending_rows, info

    try:
        from A_Lei_no_NT.models import Artigo
    except Exception as exc:  # noqa: BLE001
        info["warnings"].append(f"Não foi possível importar Artigo: {exc}")
        pending_rows = [
            build_article_pending_row(None, ws, root=root, input_dir_artigos=input_dir_artigos)
            for ws in workspace_groups.values()
        ]
        info["pending"] = len(pending_rows)
        return pending_rows, info

    try:
        artigos = list(Artigo.objects.select_related("autor", "area").all())
    except Exception as exc:  # noqa: BLE001
        info["warnings"].append(f"Falha ao ler Artigo do BD: {exc}")
        pending_rows = [
            build_article_pending_row(None, ws, root=root, input_dir_artigos=input_dir_artigos)
            for ws in workspace_groups.values()
        ]
        info["pending"] = len(pending_rows)
        return pending_rows, info

    covered_ids, covered_slugs, covered_titles = _covered_sets(sermon_rows)
    info["total_artigos_bd"] = len(artigos)
    pending_rows: list[dict] = []
    matched_workspace_keys: set[str] = set()

    for artigo in artigos:
        aid = str(getattr(artigo, "id", "") or "").strip()
        slug = str(getattr(artigo, "slug", "") or "").strip()
        title_key = normalize_lookup(str(getattr(artigo, "titulo", "") or ""))

        covered = False
        if aid and aid in covered_ids:
            covered = True
        elif slug and slug in covered_slugs:
            covered = True
        elif title_key and title_key in covered_titles:
            covered = True
        if covered:
            continue

        ws = _workspace_for_article(artigo, workspace_groups)
        if not ws:
            continue
        if ws["lookup_key"] in matched_workspace_keys:
            continue
        matched_workspace_keys.add(ws["lookup_key"])
        pending_rows.append(build_article_pending_row(artigo, ws, root=root, input_dir_artigos=input_dir_artigos))

    for key, ws in workspace_groups.items():
        if any(candidate in matched_workspace_keys for candidate in _candidate_slug_keys(key)):
            continue
        pending_rows.append(build_article_pending_row(None, ws, root=root, input_dir_artigos=input_dir_artigos))

    info["pending"] = len(pending_rows)
    return pending_rows, info
