from __future__ import annotations

import argparse
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


def main() -> int:
    ap = argparse.ArgumentParser(description='Gera snapshot JSON da publicacao do site (Artigos + Sermoes).')
    ap.add_argument('--django-settings', default='pralbinomarks.settings')
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--label', default='snapshot')
    ap.add_argument('--filename', default='')
    args = ap.parse_args()

    root = repo_root_from_here()
    setup_django(root, args.django_settings)

    from django.core.management import call_command
    from A_Lei_no_NT.models import Area, Autor, Artigo
    from sermoes.models import Sermao

    outdir = Path(args.output_dir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    fixture = outdir / (args.filename or f'publicacao_{args.label}_{stamp}.json')
    meta = outdir / f'publicacao_{args.label}_{stamp}.meta.json'

    with fixture.open('w', encoding='utf-8') as fh:
        call_command('dumpdata', 'A_Lei_no_NT.Area', 'A_Lei_no_NT.Autor', 'A_Lei_no_NT.Artigo', 'sermoes.Sermao', indent=2, stdout=fh)

    summary = {
        'fixture': str(fixture),
        'label': args.label,
        'counts': {
            'areas': Area.objects.count(),
            'autores': Autor.objects.count(),
            'artigos': Artigo.objects.count(),
            'sermoes': Sermao.objects.count(),
        },
    }
    meta.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[OK] fixture: {fixture}')
    print(f'[OK] meta   : {meta}')
    print(json.dumps(summary['counts'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
