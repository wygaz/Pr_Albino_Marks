from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

FILE_KINDS = {
    'html_a4': '__A4.html',
    'html_a5': '__A5.html',
    'html_tablet': '__tablet.html',
    'docx_a4': '__A4.docx',
    'pdf_a4': '__A4.pdf',
    'pdf_a5': '__A5.pdf',
    'pdf_tablet': '__tablet.pdf',
}

STATUS_EXECUCAO = {
    'PENDENTE',
    'DRY_RUN',
    'OK_NEW',
    'OK_UPDATED',
    'SKIP_ALREADY_PUBLISHED',
    'SKIP_INCOMPLETE',
    'SKIP_UNCHANGED',
    'ERROR',
}


@dataclass
class SermonRow:
    id_base: str
    titulo: str
    rotulo_curto: str
    slug_previsto: str
    serie: str
    autor: str
    pasta_origem: str
    pasta_relativa: str
    destino_media_rel: str
    nome_arquivo_canonico: str
    fonte_titulo: str = ''
    fonte_serie: str = ''
    fonte_autor: str = ''
    artigo_id: str = ''
    artigo_slug: str = ''
    artigo_titulo: str = ''
    artigo_visivel: bool = False
    bd_match_kind: str = ''
    html_a4_path: str = ''
    html_a5_path: str = ''
    html_tablet_path: str = ''
    docx_a4_path: str = ''
    pdf_a4_path: str = ''
    pdf_a5_path: str = ''
    pdf_tablet_path: str = ''
    html_a4_ok: bool = False
    html_a5_ok: bool = False
    html_tablet_ok: bool = False
    docx_a4_ok: bool = False
    pdf_a4_ok: bool = False
    pdf_a5_ok: bool = False
    pdf_tablet_ok: bool = False
    completo_ok: bool = False
    status_manifest: str = 'INCOMPLETO'
    duplicado_detectado: bool = False
    registro_existe: bool = False
    publicado: bool = False
    sermao_id: str = ''
    slug_atual: str = ''
    ultimo_status_execucao: str = 'PENDENTE'
    ultima_execucao_em: str = ''
    mensagem_execucao: str = ''
    assinatura_entrada: str = ''
    alterado_desde_ultima_execucao: bool = False
    criado_em: str = ''
    atualizado_em: str = ''
    origem_scan: str = ''
    observacoes: str = ''

    def to_dict(self) -> dict:
        return asdict(self)


def slugify(value: str) -> str:
    value = value.strip().lower()
    repl = {
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u',
        'ç': 'c',
    }
    for k, v in repl.items():
        value = value.replace(k, v)
    value = re.sub(r'[^a-z0-9]+', '-', value, flags=re.IGNORECASE)
    value = re.sub(r'-+', '-', value).strip('-')
    return value


def clean_title_piece(value: str) -> str:
    value = value.replace('_', ' ').replace('-', ' ')
    value = re.sub(r'\s+', ' ', value).strip()
    return value


def strip_generation_markers(base_name: str) -> str:
    value = str(base_name or '').strip()
    patterns = [
        r'__relatorio_tecnico__gpt-[^_]+',
        r'__relatorio_tecnico__.*?(?=__sermao__|$)',
        r'__sermao__gpt-[^_]+$',
        r'__gpt-[^_]+__sermao$',
        r'__gpt-[^_]+$',
    ]
    for pattern in patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)
    value = re.sub(r'__+', '__', value).strip('_')
    return value


def normalize_title_from_base(base_name: str) -> str:
    working = strip_generation_markers(base_name)
    if '__' in working:
        first = working.split('__', 1)[0]
        cleaned = clean_title_piece(first)
        if cleaned:
            return cleaned
    title = re.sub(r'__sermao__.*$', '', working, flags=re.IGNORECASE)
    title = clean_title_piece(title)
    return title or clean_title_piece(working or base_name)


def canonical_output_name(base_name: str, title: str) -> str:
    suffix = compact_suffix_from_base(base_name)
    title_slug = slugify(title or normalize_title_from_base(base_name))
    return f'{title_slug}__sermao__{suffix}' if suffix else f'{title_slug}__sermao'


def compact_suffix_from_base(base_name: str) -> str:
    patterns = [
        r'__sermao__gpt-(\d+(?:\.\d+)?)',
        r'__gpt-(\d+(?:\.\d+)?)__sermao',
        r'__gpt-(\d+(?:\.\d+)?)$',
    ]
    for pattern in patterns:
        m = re.search(pattern, base_name, flags=re.IGNORECASE)
        if m:
            return m.group(1).replace('.', '_')
    return ''


def build_short_label(title: str, base_name: str) -> str:
    # Na interface operacional, o rótulo deve ficar limpo.
    # A versão do modelo permanece na heurística do nome de arquivo final, não no título visível.
    return title


def strip_known_suffix(filename: str) -> tuple[str, Optional[str]]:
    for kind, suffix in FILE_KINDS.items():
        if filename.endswith(suffix):
            return filename[: -len(suffix)], kind
    return filename, None


def _relative_parts(path: Path, input_dir: Path) -> list[str]:
    try:
        return list(path.relative_to(input_dir).parts[:-1])
    except Exception:
        return list(path.parts[:-1])


def detect_series(path: Path, input_dir: Path) -> tuple[str, str]:
    parts = _relative_parts(path, input_dir)
    for part in reversed(parts):
        if re.search(r'^serie([_\s-].+)?$', part, flags=re.IGNORECASE):
            return part, 'pasta:serie'
    if parts:
        return parts[-1], 'pasta:ultima'
    return '', ''


def detect_author(path: Path, input_dir: Path) -> tuple[str, str]:
    parts = _relative_parts(path, input_dir)
    if len(parts) >= 2:
        return parts[-2], 'pasta:penultima'
    return '', ''


def compute_signature(files: Iterable[Path]) -> str:
    payload = []
    for file in sorted(files):
        stat = file.stat()
        payload.append(f'{file.name}|{int(stat.st_mtime)}|{stat.st_size}')
    raw = '\n'.join(payload).encode('utf-8', errors='ignore')
    return hashlib.sha1(raw).hexdigest()


def load_previous_manifest(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    if path.suffix.lower() == '.json':
        data = json.loads(path.read_text(encoding='utf-8'))
        rows = data.get('rows', data if isinstance(data, list) else [])
        return {row['id_base']: row for row in rows if row.get('id_base')}
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return {row['id_base']: row for row in reader if row.get('id_base')}


def load_overrides(path: Optional[Path]) -> Dict[str, dict]:
    if not path or not path.exists():
        return {}
    if path.suffix.lower() == '.json':
        data = json.loads(path.read_text(encoding='utf-8'))
        rows = data.get('rows', data if isinstance(data, list) else [])
        return {row['id_base']: row for row in rows if row.get('id_base')}
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return {row['id_base']: row for row in reader if row.get('id_base')}


def _pick_meta(prev: dict, overrides: dict, detected_value: str, *, field: str, detected_source: str) -> tuple[str, str]:
    if overrides.get(field):
        return str(overrides.get(field)).strip(), 'override'
    if prev.get(field):
        return str(prev.get(field)).strip(), 'manifest_anterior'
    return detected_value, detected_source


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {'1', 'true', 'yes', 'sim', 'y'}


def _relative_folder(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def refresh_row_state(row: SermonRow, *, prev_signature: str = '') -> SermonRow:
    row.completo_ok = all([
        row.html_a4_ok,
        row.html_a5_ok,
        row.html_tablet_ok,
        row.docx_a4_ok,
    ])
    row.alterado_desde_ultima_execucao = row.assinatura_entrada != str(prev_signature or '')

    observations: list[str] = []
    if row.duplicado_detectado:
        row.status_manifest = 'DUPLICADO'
        observations.append('Arquivos duplicados detectados')
    elif row.completo_ok:
        row.status_manifest = 'COMPLETO'
    else:
        row.status_manifest = 'INCOMPLETO'
        missing = []
        for key, label in [
            ('html_a4_ok', 'HTML A4'),
            ('html_a5_ok', 'HTML A5'),
            ('html_tablet_ok', 'HTML tablet'),
            ('docx_a4_ok', 'DOCX A4'),
        ]:
            if not getattr(row, key):
                missing.append(label)
        if missing:
            observations.append('Faltando: ' + ', '.join(missing))

    if row.bd_match_kind:
        observations.append(f'BD: Artigo vinculado por {row.bd_match_kind}')
    if row.nome_arquivo_canonico:
        observations.append(f'Nome sugerido: {row.nome_arquivo_canonico}')
    if not row.serie:
        observations.append('Preencher série via BD ou overrides')
    if not row.autor:
        observations.append('Preencher autor via BD ou overrides')
    if row.alterado_desde_ultima_execucao:
        observations.append('Entrada alterada desde a última execução')
    row.observacoes = ' | '.join(dict.fromkeys([o for o in observations if o]))
    return row


def scan_sermons(
    input_dir: Path,
    previous: Optional[Dict[str, dict]] = None,
    overrides: Optional[Dict[str, dict]] = None,
) -> List[SermonRow]:
    previous = previous or {}
    overrides = overrides or {}
    buckets: Dict[str, dict] = {}
    for path in input_dir.rglob('*'):
        if not path.is_file():
            continue
        base_name, kind = strip_known_suffix(path.name)
        if not kind:
            continue
        bucket = buckets.setdefault(base_name, {'files': {}, 'paths': []})
        if kind in bucket['files']:
            bucket.setdefault('duplicates', []).append(str(path))
        bucket['files'][kind] = path
        bucket['paths'].append(path)

    rows: List[SermonRow] = []
    for base_name, bucket in sorted(buckets.items()):
        first_path = sorted(bucket['paths'])[0]
        prev = previous.get(base_name, {})
        override = overrides.get(base_name, {})

        detected_title = normalize_title_from_base(base_name)
        detected_slug = slugify(detected_title)
        detected_series, detected_series_src = detect_series(first_path, input_dir)
        detected_author, detected_author_src = detect_author(first_path, input_dir)

        titulo, fonte_titulo = _pick_meta(prev, override, detected_title, field='titulo', detected_source='id_base')
        serie, fonte_serie = _pick_meta(prev, override, detected_series, field='serie', detected_source=detected_series_src)
        autor, fonte_autor = _pick_meta(prev, override, detected_author, field='autor', detected_source=detected_author_src)
        slug_previsto = (override.get('slug_previsto') or prev.get('slug_previsto') or detected_slug).strip()
        rotulo_curto = (override.get('rotulo_curto') or prev.get('rotulo_curto') or build_short_label(titulo, base_name)).strip()
        pasta_relativa = _relative_folder(first_path.parent, input_dir)
        nome_arquivo_canonico = (override.get('nome_arquivo_canonico') or prev.get('nome_arquivo_canonico') or canonical_output_name(base_name, titulo)).strip()
        destino_media_rel = (override.get('destino_media_rel') or prev.get('destino_media_rel') or f'media/sermoes/{slug_previsto}').strip()

        row = SermonRow(
            id_base=base_name,
            titulo=titulo,
            rotulo_curto=rotulo_curto,
            slug_previsto=slug_previsto,
            serie=serie,
            autor=autor,
            pasta_origem=str(first_path.parent),
            pasta_relativa=pasta_relativa,
            destino_media_rel=destino_media_rel,
            nome_arquivo_canonico=nome_arquivo_canonico,
            fonte_titulo=fonte_titulo,
            fonte_serie=fonte_serie,
            fonte_autor=fonte_autor,
            origem_scan=str(input_dir),
            registro_existe=_to_bool(override.get('registro_existe', prev.get('registro_existe'))),
            publicado=_to_bool(override.get('publicado', prev.get('publicado'))),
            sermao_id=str(override.get('sermao_id', prev.get('sermao_id', ''))),
            slug_atual=str(override.get('slug_atual', prev.get('slug_atual', ''))),
            ultimo_status_execucao=str(override.get('ultimo_status_execucao') or prev.get('ultimo_status_execucao') or 'PENDENTE'),
            ultima_execucao_em=str(override.get('ultima_execucao_em', prev.get('ultima_execucao_em', ''))),
            mensagem_execucao=str(override.get('mensagem_execucao', prev.get('mensagem_execucao', ''))),
            criado_em=str(override.get('criado_em', prev.get('criado_em', ''))),
            atualizado_em=str(override.get('atualizado_em', prev.get('atualizado_em', ''))),
            observacoes=str(override.get('observacoes', prev.get('observacoes', ''))),
            duplicado_detectado=bool(bucket.get('duplicates')),
            artigo_id=str(override.get('artigo_id', prev.get('artigo_id', ''))),
            artigo_slug=str(override.get('artigo_slug', prev.get('artigo_slug', ''))),
            artigo_titulo=str(override.get('artigo_titulo', prev.get('artigo_titulo', ''))),
            artigo_visivel=_to_bool(override.get('artigo_visivel', prev.get('artigo_visivel'))),
            bd_match_kind=str(override.get('bd_match_kind', prev.get('bd_match_kind', ''))),
        )
        for kind in FILE_KINDS:
            file = bucket['files'].get(kind)
            setattr(row, f'{kind}_path', str(file) if file else '')
            setattr(row, f'{kind}_ok', bool(file and file.exists()))

        row.assinatura_entrada = compute_signature(bucket['paths'])
        row = refresh_row_state(row, prev_signature=str(prev.get('assinatura_entrada') or ''))
        rows.append(row)
    return rows


def write_manifest_csv(rows: List[SermonRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [row.to_dict() for row in rows]
    headers = [field for field in SermonRow.__dataclass_fields__]
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        if data:
            writer.writerows(data)


def write_manifest_json(rows: List[SermonRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'rows': [row.to_dict() for row in rows],
        'count': len(rows),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def write_overrides_template_csv(rows: List[SermonRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        'id_base',
        'titulo',
        'rotulo_curto',
        'slug_previsto',
        'serie',
        'autor',
        'artigo_id',
        'artigo_slug',
        'destino_media_rel',
        'nome_arquivo_canonico',
        'publicado',
        'registro_existe',
        'slug_atual',
        'sermao_id',
        'ultimo_status_execucao',
        'observacoes',
    ]
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.to_dict().get(k, '') for k in headers})
