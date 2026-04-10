from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def repo_root_from_here() -> Path:
    cur = Path(__file__).resolve().parent
    for _ in range(12):
        if (cur / 'manage.py').exists() or (cur / '.git').exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError('Raiz do projeto nao encontrada.')


def setup_django(root: Path, settings_module: str) -> None:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    import django
    django.setup()


def field_name(field) -> str:
    try:
        return str(getattr(field, 'name', '') or '').strip()
    except Exception:
        return ''


def delete_field_file(storage, field, *, execute: bool) -> tuple[str, str]:
    name = field_name(field)
    if not name:
        return '', ''
    if not execute:
        return name, 'DRY_DELETE_FILE'
    try:
        if storage.exists(name):
            storage.delete(name)
        return name, 'FILE_DELETED'
    except Exception as exc:  # noqa: BLE001
        return name, f'FILE_ERROR: {exc}'


def delete_storage_prefixes(storage, prefixes: list[str], *, execute: bool) -> list[dict]:
    rows: list[dict] = []
    for prefix in prefixes:
        try:
            dirs, files = storage.listdir(prefix)
        except Exception:
            continue
        for rel in files:
            name = f"{prefix.rstrip('/')}/{rel}".replace('\\', '/')
            if not execute:
                rows.append({'kind': 'orphan_media', 'target': name, 'status': 'DRY_DELETE_FILE'})
                continue
            try:
                if storage.exists(name):
                    storage.delete(name)
                rows.append({'kind': 'orphan_media', 'target': name, 'status': 'FILE_DELETED'})
            except Exception as exc:  # noqa: BLE001
                rows.append({'kind': 'orphan_media', 'target': name, 'status': f'FILE_ERROR: {exc}'})
        for sub in dirs:
            nested = f"{prefix.rstrip('/')}/{sub}".replace('\\', '/')
            rows.extend(delete_storage_prefixes(storage, [nested], execute=execute))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description='Limpa a publicacao do site (Artigos + Sermoes + anexos), local ou remoto conforme o ENV_NAME ativo.')
    ap.add_argument('--django-settings', default='pralbinomarks.settings')
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--keep-taxonomy', action='store_true', help='Preserva Area e Autor.')
    ap.add_argument('--report-dir', default='')
    args = ap.parse_args()

    root = repo_root_from_here()
    setup_django(root, args.django_settings)

    from django.core.files.storage import default_storage
    from A_Lei_no_NT.models import Area, Artigo, Autor
    from sermoes.models import Sermao

    env_name = os.getenv('ENV_NAME', 'local')
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = Path(args.report_dir).resolve() if args.report_dir else root / 'Apenas_Local' / 'backups' / env_name / f'reset_{stamp}'
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / 'reset_publicacao.csv'
    json_path = report_dir / 'reset_publicacao.json'

    execute = bool(args.execute)
    rows: list[dict] = []

    artigos = list(Artigo.objects.all().order_by('id'))
    sermoes = list(Sermao.objects.all().order_by('id'))
    areas = list(Area.objects.all().order_by('id'))
    autores = list(Autor.objects.all().order_by('id'))

    for sermao in sermoes:
        for label, field in [
            ('pdf_tablet', sermao.pdf_tablet),
            ('pdf_a4', sermao.pdf_a4),
            ('pdf_a5', sermao.pdf_a5),
            ('relatorio_tecnico_pdf', sermao.relatorio_tecnico_pdf),
            ('docx_a4', sermao.docx_a4),
            ('imagem_capa', sermao.imagem_capa),
        ]:
            target, status = delete_field_file(default_storage, field, execute=execute)
            if target:
                rows.append({'kind': 'sermao_file', 'object_id': sermao.id, 'title': sermao.titulo, 'field': label, 'target': target, 'status': status})
        rows.append({'kind': 'sermao_record', 'object_id': sermao.id, 'title': sermao.titulo, 'target': sermao.slug, 'status': 'DRY_DELETE_RECORD' if not execute else 'RECORD_DELETED'})
        if execute:
            sermao.delete()

    for artigo in artigos:
        for label, field in [
            ('arquivo_word', artigo.arquivo_word),
            ('arquivo_pdf', artigo.arquivo_pdf),
            ('imagem_capa', artigo.imagem_capa),
        ]:
            target, status = delete_field_file(default_storage, field, execute=execute)
            if target:
                rows.append({'kind': 'artigo_file', 'object_id': artigo.id, 'title': artigo.titulo, 'field': label, 'target': target, 'status': status})
        rows.append({'kind': 'artigo_record', 'object_id': artigo.id, 'title': artigo.titulo, 'target': artigo.slug, 'status': 'DRY_DELETE_RECORD' if not execute else 'RECORD_DELETED'})
        if execute:
            artigo.delete()

    if not args.keep_taxonomy:
        for area in areas:
            rows.append({'kind': 'area_record', 'object_id': area.id, 'title': getattr(area, 'nome', ''), 'target': getattr(area, 'nome', ''), 'status': 'DRY_DELETE_RECORD' if not execute else 'RECORD_DELETED'})
            if execute:
                area.delete()
        for autor in autores:
            rows.append({'kind': 'autor_record', 'object_id': autor.id, 'title': getattr(autor, 'nome', ''), 'target': getattr(autor, 'nome', ''), 'status': 'DRY_DELETE_RECORD' if not execute else 'RECORD_DELETED'})
            if execute:
                autor.delete()

    prefixes = [
        'uploads/artigos',
        'pdfs/artigos',
        'imagens/artigos',
        'pdfs/sermoes',
        'pdfs/relatorios_tecnicos',
        'docs/sermoes',
        'imagens/sermoes',
    ]
    rows.extend(delete_storage_prefixes(default_storage, prefixes, execute=execute))

    fieldnames = ['kind', 'object_id', 'title', 'field', 'target', 'status']
    with csv_path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in fieldnames})

    payload = {
        'env_name': env_name,
        'execute': execute,
        'keep_taxonomy': args.keep_taxonomy,
        'csv_path': str(csv_path),
        'counts_before': {
            'artigos': len(artigos),
            'sermoes': len(sermoes),
            'areas': len(areas),
            'autores': len(autores),
        },
        'rows': rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] CSV : {csv_path}')
    print(f'[OK] JSON: {json_path}')
    print(json.dumps(payload['counts_before'], ensure_ascii=False))
    if not execute:
        print('[INFO] Nenhuma alteracao executada. Rode novamente com --execute para aplicar.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
