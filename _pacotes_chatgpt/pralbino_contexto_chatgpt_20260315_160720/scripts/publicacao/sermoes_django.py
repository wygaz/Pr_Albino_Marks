from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from sermoes_inventory import SermonRow


def detect_settings_module(root: Path) -> str:
    explicit = [
        (root / 'pralbinomarks' / 'settings.py', 'pralbinomarks.settings'),
    ]
    for settings_path, module in explicit:
        if settings_path.exists():
            return module
    for candidate in sorted(root.glob('*/settings.py')):
        pkg = candidate.parent.name
        return f'{pkg}.settings'
    return ''


def normalize_lookup(value: str) -> str:
    from sermoes_inventory import clean_title_piece, slugify

    return slugify(clean_title_piece(value or ''))


def candidate_slug_keys(row: SermonRow) -> list[str]:
    from sermoes_inventory import normalize_title_from_base, slugify, strip_generation_markers

    values = [
        row.slug_previsto,
        row.artigo_slug,
        slugify(row.titulo or ''),
        slugify(row.rotulo_curto or ''),
        slugify(normalize_title_from_base(row.id_base or '')),
        slugify(strip_generation_markers(row.id_base or '')),
    ]
    out = []
    for value in values:
        value = (value or '').strip()
        if value and value not in out:
            out.append(value)
    return out


def candidate_title_keys(row: SermonRow) -> list[str]:
    from sermoes_inventory import normalize_title_from_base, strip_generation_markers

    values = [
        row.titulo,
        row.rotulo_curto,
        normalize_title_from_base(row.id_base or ''),
        strip_generation_markers(row.id_base or ''),
        row.artigo_titulo,
    ]
    out = []
    for value in values:
        key = normalize_lookup(value or '')
        if key and key not in out:
            out.append(key)
    return out


def setup_django(root: Path, settings_module: str | None = None) -> str:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    module = settings_module or os.environ.get('DJANGO_SETTINGS_MODULE') or detect_settings_module(root)
    if not module:
        raise RuntimeError('Não foi possível detectar DJANGO_SETTINGS_MODULE automaticamente.')

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', module)

    import django

    django.setup()
    return module


def hydrate_rows_from_django(
    rows: list[SermonRow],
    root: Path,
    settings_module: str | None = None,
) -> dict[str, Any]:
    """
    Hidrata metadados do manifest a partir do BD Django.

    Regra operacional acordada:
      override manual -> manifest anterior -> BD -> heurística da pasta

    Como o inventário já pode ter preenchido série/autor por heurística,
    o BD só sobrescreve quando a fonte atual estiver vazia ou vier de pasta.
    """
    info: dict[str, Any] = {
        'enabled': False,
        'settings_module': '',
        'matched': 0,
        'filled_serie': 0,
        'filled_autor': 0,
        'filled_titulo': 0,
        'warnings': [],
    }

    try:
        module = setup_django(root, settings_module)
        info['enabled'] = True
        info['settings_module'] = module
    except Exception as exc:  # noqa: BLE001
        info['warnings'].append(f'BD indisponível: {exc}')
        return info

    try:
        from A_Lei_no_NT.models import Artigo
    except Exception as exc:  # noqa: BLE001
        info['warnings'].append(f'Não foi possível importar A_Lei_no_NT.models.Artigo: {exc}')
        return info

    try:
        artigos = list(
            Artigo.objects.select_related('autor', 'area').all()
        )
    except Exception as exc:  # noqa: BLE001
        info['warnings'].append(f'Falha ao ler Artigo do BD: {exc}')
        return info

    by_slug: dict[str, Any] = {}
    by_title: dict[str, list[Any]] = {}
    for artigo in artigos:
        slug = (getattr(artigo, 'slug', '') or '').strip()
        title = (getattr(artigo, 'titulo', '') or '').strip()
        if slug:
            by_slug[slug] = artigo
        norm_title = normalize_lookup(title)
        if norm_title:
            by_title.setdefault(norm_title, []).append(artigo)

    for row in rows:
        artigo = None
        match_kind = ''

        for slug_key in candidate_slug_keys(row):
            if slug_key in by_slug:
                artigo = by_slug[slug_key]
                match_kind = 'slug'
                break

        if not artigo:
            for slug_key in candidate_slug_keys(row):
                prefix_hits = [a for s, a in by_slug.items() if s.startswith(slug_key) or slug_key.startswith(s)]
                uniq = {getattr(a, 'id', None): a for a in prefix_hits}
                if len(uniq) == 1:
                    artigo = next(iter(uniq.values()))
                    match_kind = 'slug_prefix'
                    break

        if not artigo:
            for title_key in candidate_title_keys(row):
                title_hits = by_title.get(title_key, [])
                if len(title_hits) == 1:
                    artigo = title_hits[0]
                    match_kind = 'titulo'
                    break
                if len(title_hits) > 1:
                    row.observacoes = ' | '.join(
                        dict.fromkeys(
                            [
                                x
                                for x in [
                                    row.observacoes,
                                    'Título ambíguo no BD: mais de um Artigo correspondente',
                                ]
                                if x
                            ]
                        )
                    )

        if not artigo:
            continue

        info['matched'] += 1
        row.artigo_id = str(getattr(artigo, 'id', '') or '')
        row.artigo_slug = (getattr(artigo, 'slug', '') or '').strip()
        row.artigo_titulo = (getattr(artigo, 'titulo', '') or '').strip()
        row.artigo_visivel = bool(getattr(artigo, 'visivel', False))
        row.bd_match_kind = match_kind

        area_obj = getattr(artigo, 'area', None)
        autor_obj = getattr(artigo, 'autor', None)

        if area_obj and (not row.serie or (row.fonte_serie or '').startswith('pasta')):
            row.serie = str(getattr(area_obj, 'nome', '') or '').strip()
            row.fonte_serie = 'bd:area'
            info['filled_serie'] += 1

        if autor_obj and (not row.autor or (row.fonte_autor or '').startswith('pasta')):
            row.autor = str(getattr(autor_obj, 'nome', '') or '').strip()
            row.fonte_autor = 'bd:autor'
            info['filled_autor'] += 1

        if row.artigo_titulo and (not row.titulo or row.fonte_titulo == 'id_base'):
            row.titulo = row.artigo_titulo
            row.fonte_titulo = 'bd:titulo'
            info['filled_titulo'] += 1

    return info
