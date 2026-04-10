from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from artigos_operacional_utils import strip_editorial_prefixes

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


def clean_workspace_stem(value: str) -> str:
    text = Path(value or '').stem
    text = re.sub(r'__dossie$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'__relatorio_tecnico__.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'__sermao__.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\d{1,3}__+', '', text)
    text = re.sub(r'^\d{1,3}_+', '', text)
    text = strip_editorial_prefixes(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip(' _-') or 'sermao'


def ascii_slug(text: str) -> str:
    import unicodedata
    value = unicodedata.normalize('NFKD', text or '')
    value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^A-Za-z0-9]+', '-', value).strip('-').lower()
    return value or 'sermao'


def guess_title_from_slug(stem: str) -> str:
    base = clean_workspace_stem(stem).replace('-', ' ')
    return ' '.join(part.capitalize() for part in base.split())


def main() -> int:
    ap = argparse.ArgumentParser(description='Publica em lote os sermoes formatados ja gerados.')
    ap.add_argument('--sermoes-formatados-root', default='')
    ap.add_argument('--dossies-formatados-root', default='')
    ap.add_argument('--publish-script', required=True)
    ap.add_argument('--django-settings', default='pralbinomarks.settings')
    ap.add_argument('--python-exe', default=sys.executable)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--report-csv', default='')
    ap.add_argument('--overwrite-media', action='store_true')
    args = ap.parse_args()

    root = repo_root_from_here()
    setup_django(root, args.django_settings)
    from A_Lei_no_NT.models import Artigo

    sermoes_root = Path(args.sermoes_formatados_root).resolve() if args.sermoes_formatados_root else root / 'Apenas_Local' / 'operacional' / 'sermoes' / 'formatados'
    dossies_root = Path(args.dossies_formatados_root).resolve() if args.dossies_formatados_root else root / 'Apenas_Local' / 'operacional' / 'dossies' / 'formatados'
    publish_script = Path(args.publish_script).resolve()
    if not publish_script.exists():
        raise FileNotFoundError(f'Publish script nao encontrado: {publish_script}')

    htmls = sorted(sermoes_root.rglob('*__sermao__a4.html'))
    if args.limit:
        htmls = htmls[:args.limit]

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_csv = Path(args.report_csv).resolve() if args.report_csv else root / 'Apenas_Local' / 'backups' / 'local' / f'publicacao_sermoes_lote_{stamp}.csv'
    report_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    total = len(htmls)
    if not total:
        print('[INFO] Nenhum sermao A4 encontrado para publicacao em lote.')
        return 0

    for idx, html_a4 in enumerate(htmls, start=1):
        stem = html_a4.name.replace('__sermao__a4.html', '')
        base_slug = ascii_slug(clean_workspace_stem(stem))
        artigo = Artigo.objects.filter(slug=base_slug).first()
        titulo = (artigo.titulo if artigo else guess_title_from_slug(stem))
        serie = (getattr(getattr(artigo, 'area', None), 'nome', '') or '').strip()
        ordem_match = re.match(r'^(\d{1,3})__', stem)
        ordem = int(ordem_match.group(1)) if ordem_match else 0
        resumo = ''
        html_a5 = html_a4.with_name(html_a4.name.replace('__a4.html', '__a5.html'))
        html_tablet = html_a4.with_name(html_a4.name.replace('__a4.html', '__tablet.html'))
        docx_a4 = html_a4.with_name(html_a4.name.replace('__a4.html', '__a4.docx'))
        relatorio_html = dossies_root / html_a4.relative_to(sermoes_root)
        relatorio_html = relatorio_html.with_name(relatorio_html.name.replace('__sermao__a4.html', '__dossie__a4.html'))

        cmd = [
            args.python_exe, str(publish_script),
            '--titulo', titulo,
            '--serie', serie,
            '--resumo', resumo,
            '--slug', base_slug,
            '--ordem', str(ordem),
            '--html-a4', str(html_a4),
        ]
        if html_a5.exists():
            cmd.extend(['--html-a5', str(html_a5)])
        if html_tablet.exists():
            cmd.extend(['--html-tablet', str(html_tablet)])
        if docx_a4.exists():
            cmd.extend(['--docx-a4', str(docx_a4)])
        if relatorio_html.exists():
            cmd.extend(['--relatorio-html', str(relatorio_html)])

        print(f'[{idx}/{total}] Publicar sermao: {titulo} | slug={base_slug}')
        proc = subprocess.run(cmd, text=True, capture_output=True)
        status = 'OK' if proc.returncode == 0 else 'ERRO'
        rows.append({
            'index': idx,
            'titulo': titulo,
            'slug': base_slug,
            'serie': serie,
            'html_a4': str(html_a4),
            'status': status,
            'returncode': proc.returncode,
            'stdout': proc.stdout.strip(),
            'stderr': proc.stderr.strip(),
        })
        if proc.stdout:
            print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        if proc.returncode != 0:
            print(f'[ERRO] Falha ao publicar {base_slug}.')

    with report_csv.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['index', 'titulo', 'slug', 'serie', 'html_a4', 'status', 'returncode', 'stdout', 'stderr'])
        writer.writeheader()
        writer.writerows(rows)
    print(f'[OK] Relatorio CSV: {report_csv}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
