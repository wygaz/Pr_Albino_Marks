from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline_steps import parse_operation_spec
from sermoes_django import normalize_lookup, setup_django

ARTICLE_EXTS = {'.docx', '.html', '.htm', '.pdf', '.md', '.txt'}


def _covered_sets(sermon_rows: list[dict]) -> tuple[set[str], set[str], set[str]]:
    ids: set[str] = set()
    slugs: set[str] = set()
    titles: set[str] = set()
    for row in sermon_rows:
        for value in [row.get('artigo_id'), row.get('sermao_id')]:
            value = str(value or '').strip()
            if value:
                ids.add(value)
        for value in [row.get('artigo_slug'), row.get('slug_previsto')]:
            value = str(value or '').strip()
            if value:
                slugs.add(value)
        for value in [row.get('titulo'), row.get('rotulo_curto'), row.get('artigo_titulo')]:
            key = normalize_lookup(str(value or ''))
            if key:
                titles.add(key)
    return ids, slugs, titles


def _clean_workspace_stem(path: Path) -> str:
    stem = path.stem
    for suffix in ['__A4', '__A5', '__tablet', '_A4', '_A5', '_tablet', '__a4', '__a5']:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem.strip(' _-')


def scan_article_workspace(input_dir: Path | None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    info: dict[str, Any] = {'enabled': False, 'base_dir': '', 'files': 0, 'groups': 0, 'warnings': []}
    if not input_dir:
        return {}, info
    input_dir = Path(input_dir)
    if not input_dir.exists():
        info['warnings'].append(f'InputDirArtigos não encontrado: {input_dir}')
        return {}, info

    info['enabled'] = True
    info['base_dir'] = str(input_dir)
    groups: dict[str, dict[str, Any]] = {}
    for path in input_dir.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in ARTICLE_EXTS:
            continue
        info['files'] += 1
        raw_stem = _clean_workspace_stem(path)
        key = normalize_lookup(raw_stem)
        if not key:
            continue
        rel = path.relative_to(input_dir).as_posix()
        entry = groups.setdefault(
            key,
            {
                'lookup_key': key,
                'display_name': raw_stem,
                'paths': [],
                'paths_rel': [],
                'docx_path': '',
                'html_path': '',
                'pdf_path': '',
                'source_types': set(),
            },
        )
        entry['paths'].append(str(path))
        entry['paths_rel'].append(rel)
        suffix = path.suffix.lower()
        if suffix == '.docx' and not entry['docx_path']:
            entry['docx_path'] = str(path)
        elif suffix in {'.html', '.htm'} and not entry['html_path']:
            entry['html_path'] = str(path)
        elif suffix == '.pdf' and not entry['pdf_path']:
            entry['pdf_path'] = str(path)
        entry['source_types'].add(suffix.lstrip('.'))
    info['groups'] = len(groups)
    return groups, info


def _workspace_for_article(artigo: Any, groups: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    candidates = []
    for value in [getattr(artigo, 'slug', ''), getattr(artigo, 'titulo', '')]:
        key = normalize_lookup(str(value or ''))
        if key:
            candidates.append(key)
    for key in candidates:
        if key in groups:
            return groups[key]
    return None


def _infer_completed_steps(workspace: dict[str, Any] | None) -> list[int]:
    if not workspace:
        return []
    steps: set[int] = set()
    source_types = set((workspace or {}).get('source_types', set()) or set())
    if 'md' in source_types:
        steps.add(3)
    if workspace.get('docx_path'):
        steps.add(4)
    if workspace.get('html_path'):
        steps.add(6)
    if workspace.get('pdf_path'):
        steps.add(7)
    return sorted(steps)


def _steps_as_text(steps: list[int]) -> str:
    return ','.join(str(s) for s in steps)


def _stage_from_workspace(workspace: dict[str, Any] | None) -> tuple[str, list[int], str, list[int], str]:
    completed = _infer_completed_steps(workspace)
    completed_text = _steps_as_text(completed)
    if not workspace:
        plan = parse_operation_spec('1-8')
        return 'SEM_INSUMOS_LOCAIS', plan.steps, plan.normalized, completed, completed_text
    if workspace.get('pdf_path'):
        plan = parse_operation_spec('8')
        return 'PDF_LOCALIZADO', plan.steps, plan.normalized, completed, completed_text
    if workspace.get('html_path'):
        plan = parse_operation_spec('7-8')
        return 'HTML_LOCALIZADO', plan.steps, plan.normalized, completed, completed_text
    if workspace.get('docx_path'):
        plan = parse_operation_spec('5-8')
        return 'DOCX_LOCALIZADO', plan.steps, plan.normalized, completed, completed_text
    if completed:
        start = min(max(completed[-1] + 1, 1), 8)
        plan = parse_operation_spec(f'{start}-8') if start < 8 else parse_operation_spec('8')
        return 'PENDENTE_PARCIAL', plan.steps, plan.normalized, completed, completed_text
    plan = parse_operation_spec('1-8')
    return 'PENDENTE', plan.steps, plan.normalized, completed, completed_text


def build_article_pending_row(artigo: Any | None, workspace: dict[str, Any] | None, input_dir_artigos: Path | None = None) -> dict[str, Any]:
    titulo = (str(getattr(artigo, 'titulo', '') or '') if artigo is not None else str((workspace or {}).get('display_name', '') or '')).strip()
    slug = (str(getattr(artigo, 'slug', '') or '') if artigo is not None else normalize_lookup(titulo).replace('_', '-')).strip()
    area_obj = getattr(artigo, 'area', None) if artigo is not None else None
    autor_obj = getattr(artigo, 'autor', None) if artigo is not None else None
    serie = str(getattr(area_obj, 'nome', '') or '').strip()
    autor = str(getattr(autor_obj, 'nome', '') or '').strip()
    etapa_atual, operacao_steps, operacao_spec, etapas_concluidas, etapas_concluidas_texto = _stage_from_workspace(workspace)
    source_types = ', '.join(sorted((workspace or {}).get('source_types', [])))
    rel_paths = ', '.join((workspace or {}).get('paths_rel', [])[:3])
    lookup_key = normalize_lookup(slug or titulo)
    return {
        'context': 'artigos_sem_sermao',
        'id_base': f'artigo__{getattr(artigo, "id", lookup_key or "arquivo")}',
        'titulo': titulo,
        'rotulo_curto': titulo,
        'slug_previsto': slug,
        'serie': serie,
        'autor': autor,
        'pasta_origem': str(input_dir_artigos or ''),
        'pasta_relativa': rel_paths,
        'destino_media_rel': f'media/sermoes/{slug}' if slug else '',
        'nome_arquivo_canonico': f'{slug}__sermao__5' if slug else '',
        'fonte_titulo': 'bd:titulo' if artigo is not None else 'workspace:arquivo',
        'fonte_serie': 'bd:area' if serie else '',
        'fonte_autor': 'bd:autor' if autor else '',
        'artigo_id': str(getattr(artigo, 'id', '') or ''),
        'artigo_slug': slug,
        'artigo_titulo': titulo,
        'artigo_visivel': bool(getattr(artigo, 'visivel', False)) if artigo is not None else False,
        'bd_match_kind': 'artigo_pendente' if artigo is not None else 'workspace_sem_bd',
        'workspace_docx_path': (workspace or {}).get('docx_path', ''),
        'workspace_html_path': (workspace or {}).get('html_path', ''),
        'workspace_pdf_path': (workspace or {}).get('pdf_path', ''),
        'workspace_source_types': source_types,
        'workspace_lookup_key': lookup_key,
        'html_a4_path': '',
        'html_a5_path': '',
        'html_tablet_path': '',
        'docx_a4_path': '',
        'pdf_a4_path': '',
        'pdf_a5_path': '',
        'pdf_tablet_path': '',
        'html_a4_ok': False,
        'html_a5_ok': False,
        'html_tablet_ok': False,
        'docx_a4_ok': False,
        'pdf_a4_ok': False,
        'pdf_a5_ok': False,
        'pdf_tablet_ok': False,
        'completo_ok': False,
        'status_manifest': 'SEM_SERMAO',
        'duplicado_detectado': False,
        'registro_existe': False,
        'publicado': False,
        'sermao_id': '',
        'slug_atual': slug,
        'ultimo_status_execucao': 'PENDENTE_GERACAO',
        'ultima_execucao_em': '',
        'mensagem_execucao': '',
        'assinatura_entrada': '',
        'alterado_desde_ultima_execucao': False,
        'criado_em': '',
        'atualizado_em': '',
        'origem_scan': 'bd:Artigo' if artigo is not None else 'workspace:artigo',
        'etapa_atual': etapa_atual,
        'operacao_recomendada': operacao_spec,
        'operacao_steps': operacao_steps,
        'etapas_concluidas_inferidas': etapas_concluidas,
        'etapas_concluidas_texto': etapas_concluidas_texto,
        'ultima_operacao_solicitada': '',
        'historico_operacoes': '',
        'observacoes': (
            f'Pendência pronta para geração em lote. Fontes locais: {source_types or "nenhuma"}. '
            f'Etapas concluídas (inferidas): {etapas_concluidas_texto or "nenhuma"}. '
            f'Execute operações {operacao_spec or "1-8"} conforme necessário.'
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
        'enabled': False,
        'settings_module': '',
        'total_artigos': 0,
        'pending': 0,
        'warnings': [],
        'workspace_enabled': False,
        'workspace_groups': 0,
    }

    workspace_base = workspace_artigos or input_dir_artigos
    workspace_groups, workspace_info = scan_article_workspace(workspace_base)
    info['workspace_enabled'] = workspace_info.get('enabled', False)
    info['workspace_groups'] = workspace_info.get('groups', 0)
    info['warnings'].extend(workspace_info.get('warnings', []))

    try:
        module = setup_django(root, settings_module)
        info['enabled'] = True
        info['settings_module'] = module
    except Exception as exc:  # noqa: BLE001
        info['warnings'].append(f'BD indisponível para artigos: {exc}')
        # fallback: only workspace rows
        pending_rows = [
            build_article_pending_row(None, ws, input_dir_artigos=input_dir_artigos)
            for ws in workspace_groups.values()
        ]
        info['pending'] = len(pending_rows)
        return pending_rows, info

    try:
        from A_Lei_no_NT.models import Artigo
    except Exception as exc:  # noqa: BLE001
        info['warnings'].append(f'Não foi possível importar Artigo: {exc}')
        pending_rows = [
            build_article_pending_row(None, ws, input_dir_artigos=input_dir_artigos)
            for ws in workspace_groups.values()
        ]
        info['pending'] = len(pending_rows)
        return pending_rows, info

    try:
        artigos = list(Artigo.objects.select_related('autor', 'area').all())
    except Exception as exc:  # noqa: BLE001
        info['warnings'].append(f'Falha ao ler Artigo do BD: {exc}')
        pending_rows = [
            build_article_pending_row(None, ws, input_dir_artigos=input_dir_artigos)
            for ws in workspace_groups.values()
        ]
        info['pending'] = len(pending_rows)
        return pending_rows, info

    covered_ids, covered_slugs, covered_titles = _covered_sets(sermon_rows)
    info['total_artigos'] = len(artigos)
    pending_rows: list[dict] = []
    matched_workspace_keys: set[str] = set()

    for artigo in artigos:
        aid = str(getattr(artigo, 'id', '') or '').strip()
        slug = str(getattr(artigo, 'slug', '') or '').strip()
        title_key = normalize_lookup(str(getattr(artigo, 'titulo', '') or ''))

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
        if ws:
            matched_workspace_keys.add(ws['lookup_key'])
        pending_rows.append(build_article_pending_row(artigo, ws, input_dir_artigos=input_dir_artigos))

    for key, ws in workspace_groups.items():
        if key in matched_workspace_keys:
            continue
        pending_rows.append(build_article_pending_row(None, ws, input_dir_artigos=input_dir_artigos))

    info['pending'] = len(pending_rows)
    return pending_rows, info
