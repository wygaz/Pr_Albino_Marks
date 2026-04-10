from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse


def repo_root_from_here() -> Path:
    cur = Path(__file__).resolve().parent
    for _ in range(12):
        if (cur / 'manage.py').exists() or (cur / '.git').exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError('Raiz do projeto nao encontrada.')


def parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.lower().startswith('export '):
            line = line[7:].strip()
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        data[key] = value
    return data


def info_for_profile(env_name: str) -> dict:
    root = repo_root_from_here()
    env_path = root / f'.env.{env_name}'
    env_data = parse_env_file(env_path)
    db_url = env_data.get('DATABASE_URL') or env_data.get('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL') or os.getenv('DATABASE_PUBLIC_URL')
    if not db_url:
        raise RuntimeError(f'DATABASE_URL nao encontrado em {env_path.name}.')

    parsed = urlparse(db_url)
    query = dict(parse_qsl(parsed.query))
    scheme = parsed.scheme
    if scheme not in {'postgres', 'postgresql'}:
        raise RuntimeError(f'Esquema de banco nao suportado: {scheme}')

    return {
        'env_name': env_name,
        'env_path': str(env_path),
        'database_url': db_url,
        'scheme': scheme,
        'host': parsed.hostname or '',
        'port': str(parsed.port or 5432),
        'database': (parsed.path or '/').lstrip('/'),
        'user': unquote(parsed.username or ''),
        'password': unquote(parsed.password or ''),
        'sslmode': query.get('sslmode', ''),
        'bucket': env_data.get('S3_BUCKET_NAME') or env_data.get('AWS_STORAGE_BUCKET_NAME', ''),
        'use_s3': (env_data.get('USE_S3') or env_data.get('USE_S3_FOR_MEDIA') or '0').strip().lower() in {'1', 'true', 'yes'},
        'aws_profile': env_data.get('AWS_PROFILE', ''),
        'aws_region': env_data.get('AWS_DEFAULT_REGION') or env_data.get('AWS_S3_REGION_NAME', ''),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description='Extrai informacoes do DATABASE_URL e S3 de um perfil .env.<nome>.')
    ap.add_argument('--env-name', required=True, choices=['local', 'remoto'])
    ap.add_argument('--field', default='json', help='json | host | port | database | user | password | bucket | use_s3 | env_path')
    args = ap.parse_args()

    data = info_for_profile(args.env_name)
    if args.field == 'json':
        print(json.dumps(data, ensure_ascii=False))
        return 0
    value = data.get(args.field)
    if value is None:
        raise SystemExit(f'Campo invalido: {args.field}')
    if isinstance(value, bool):
        print('1' if value else '0')
    else:
        print(value)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
