from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from artigos_django import fetch_articles_without_sermon
from sermoes_browse import generate_browse_html
from sermoes_django import hydrate_rows_from_django
from sermoes_inventory import (
    load_overrides,
    load_previous_manifest,
    refresh_row_state,
    scan_sermons,
    write_manifest_csv,
    write_manifest_json,
    write_overrides_template_csv,
)
from sermoes_runner import execute_rows, filter_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Orquestrador de sermões — Etapa 2')
    parser.add_argument('--root', default='.')
    parser.add_argument('--input-dir', required=True, help='Pasta dos sermões formatados')
    parser.add_argument('--input-dir-artigos', help='Pasta-base dos artigos/insumos para geração de sermão')
    parser.add_argument('--workspace-artigos', help='Workspace operacional dos artigos (opcional; default = input-dir-artigos)')
    parser.add_argument('--manifest-csv')
    parser.add_argument('--manifest-json')
    parser.add_argument('--manifest-overrides', help='CSV/JSON com metadados corrigidos por id_base (titulo, serie, autor, slug_previsto etc.)')
    parser.add_argument('--manifest-overrides-template', help='CSV gerado automaticamente para preenchimento manual de metadados')
    parser.add_argument('--articles-manifest-csv')
    parser.add_argument('--articles-manifest-json')
    parser.add_argument('--browse-html')
    parser.add_argument('--selection-file')
    parser.add_argument('--scan-only', action='store_true')
    parser.add_argument('--browse', action='store_true')
    parser.add_argument('--open-browse', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--serie')
    parser.add_argument('--autor')
    parser.add_argument('--pasta')
    parser.add_argument('--search')
    parser.add_argument('--status-manifest')
    parser.add_argument('--status-execucao')
    parser.add_argument('--only-published', action='store_true')
    parser.add_argument('--only-unpublished', action='store_true')
    parser.add_argument('--only-changed', action='store_true')
    parser.add_argument('--retry-failed', action='store_true')
    parser.add_argument('--continue-on-error', action='store_true')
    parser.add_argument('--skip-if-exists', action='store_true')
    parser.add_argument('--runner-template')
    parser.add_argument('--unit-script')
    parser.add_argument('--resumo-padrao')
    parser.add_argument('--log-file')
    parser.add_argument('--report-csv')
    parser.add_argument('--django-settings', help='Ex.: pralbinomarks.settings')
    parser.add_argument('--no-db-hydrate', action='store_true', help='Desliga a hidratação do manifest pelo BD Django')
    parser.add_argument('--no-articles-context', action='store_true', help='Não gera o contexto Artigos sem sermão no browse')
    return parser.parse_args()


def default_paths(root: Path) -> dict:
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = root / 'Apenas_Local'
    return {
        'manifest_csv': base / 'manifests' / 'manifest_sermoes.csv',
        'manifest_json': base / 'manifests' / 'manifest_sermoes.json',
        'manifest_overrides': base / 'manifests' / 'manifest_sermoes_overrides.csv',
        'manifest_overrides_template': base / 'manifests' / 'manifest_sermoes_overrides_modelo.csv',
        'articles_manifest_csv': base / 'manifests' / 'manifest_artigos_sem_sermao.csv',
        'articles_manifest_json': base / 'manifests' / 'manifest_artigos_sem_sermao.json',
        'browse_html': base / 'browse' / 'manifest_sermoes.html',
        'log_file': base / 'logs' / f'publicacao_sermoes_lote_{stamp}.log',
        'report_csv': base / 'relatorios' / f'relatorio_lote_{stamp}.csv',
    }


def open_file(path: Path) -> None:
    try:
        if sys.platform.startswith('win'):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(path)], check=False)
        else:
            subprocess.run(['xdg-open', str(path)], check=False)
    except Exception:
        pass


def summarize_rows(rows: list[dict]) -> dict:
    status_manifest = {}
    status_execucao = {}
    for row in rows:
        status_manifest[row.get('status_manifest', '')] = status_manifest.get(row.get('status_manifest', ''), 0) + 1
        status_execucao[row.get('ultimo_status_execucao', '')] = status_execucao.get(row.get('ultimo_status_execucao', ''), 0) + 1
    return {
        'total': len(rows),
        'publicados': sum(1 for r in rows if r.get('publicado')),
        'completos': sum(1 for r in rows if r.get('completo_ok')),
        'alterados': sum(1 for r in rows if r.get('alterado_desde_ultima_execucao')),
        'sem_serie': sum(1 for r in rows if not r.get('serie')),
        'sem_autor': sum(1 for r in rows if not r.get('autor')),
        'com_match_bd': sum(1 for r in rows if r.get('artigo_id')),
        'status_manifest': status_manifest,
        'status_execucao': status_execucao,
    }


def write_rows_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    headers: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in headers:
                headers.append(key)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_rows_json(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {'rows': rows, 'count': len(rows)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    input_dir = Path(args.input_dir).resolve()
    input_dir_artigos = Path(args.input_dir_artigos).resolve() if args.input_dir_artigos else None
    workspace_artigos = Path(args.workspace_artigos).resolve() if args.workspace_artigos else input_dir_artigos
    paths = default_paths(root)
    manifest_csv = Path(args.manifest_csv) if args.manifest_csv else paths['manifest_csv']
    manifest_json = Path(args.manifest_json) if args.manifest_json else paths['manifest_json']
    articles_manifest_csv = Path(args.articles_manifest_csv) if args.articles_manifest_csv else paths['articles_manifest_csv']
    articles_manifest_json = Path(args.articles_manifest_json) if args.articles_manifest_json else paths['articles_manifest_json']
    browse_html = Path(args.browse_html) if args.browse_html else paths['browse_html']
    log_file = Path(args.log_file) if args.log_file else paths['log_file']
    report_csv = Path(args.report_csv) if args.report_csv else paths['report_csv']
    overrides_path = Path(args.manifest_overrides) if args.manifest_overrides else paths['manifest_overrides']
    overrides_template_path = Path(args.manifest_overrides_template) if args.manifest_overrides_template else paths['manifest_overrides_template']

    previous = load_previous_manifest(manifest_json if manifest_json.exists() else manifest_csv)
    overrides = load_overrides(overrides_path)
    rows = scan_sermons(input_dir, previous=previous, overrides=overrides)

    db_info = {'enabled': False, 'warnings': []}
    if not args.no_db_hydrate:
        db_info = hydrate_rows_from_django(rows, root=root, settings_module=args.django_settings)
        for row in rows:
            prev_signature = previous.get(row.id_base, {}).get('assinatura_entrada', '')
            refresh_row_state(row, prev_signature=str(prev_signature or ''))

    write_manifest_csv(rows, manifest_csv)
    write_manifest_json(rows, manifest_json)
    write_overrides_template_csv(rows, overrides_template_path)
    sermon_rows_dict = [r.to_dict() for r in rows]
    summary_scan = summarize_rows(sermon_rows_dict)

    print(f'[OK] InputDir Sermões: {input_dir}')
    if input_dir_artigos:
        print(f'[OK] InputDir Artigos: {input_dir_artigos}')
    if workspace_artigos:
        print(f'[OK] Workspace Artigos: {workspace_artigos}')
    print(f'[OK] Manifest CSV: {manifest_csv}')
    print(f'[OK] Manifest JSON: {manifest_json}')
    print(f'[OK] Modelo de overrides: {overrides_template_path}')
    print(f"[OK] Itens encontrados: {summary_scan['total']}")
    print(f"[OK] Completos: {summary_scan['completos']} | Publicados: {summary_scan['publicados']} | Alterados: {summary_scan['alterados']}")
    print(f"[OK] Sem série: {summary_scan['sem_serie']} | Sem autor: {summary_scan['sem_autor']} | Match BD: {summary_scan['com_match_bd']}")
    if overrides_path.exists():
        print(f'[OK] Overrides aplicados: {overrides_path}')
    else:
        print(f'[INFO] Overrides ainda não encontrados. Preencha, se desejar: {overrides_path}')

    if db_info.get('enabled'):
        print(f"[OK] BD hidratado via {db_info.get('settings_module')} | match={db_info.get('matched', 0)} | série(area)={db_info.get('filled_serie', 0)} | autor={db_info.get('filled_autor', 0)}")
    for warning in db_info.get('warnings', []):
        print(f'[WARN] {warning}')

    article_rows: list[dict] = []
    articles_info = {'enabled': False, 'warnings': []}
    if not args.no_articles_context and not args.no_db_hydrate:
        article_rows, articles_info = fetch_articles_without_sermon(
            root=root,
            settings_module=args.django_settings,
            sermon_rows=sermon_rows_dict,
            input_dir_artigos=input_dir_artigos,
            workspace_artigos=workspace_artigos,
        )
        write_rows_csv(article_rows, articles_manifest_csv)
        write_rows_json(article_rows, articles_manifest_json)
        print(f'[OK] Manifest Artigos CSV: {articles_manifest_csv}')
        print(f'[OK] Manifest Artigos JSON: {articles_manifest_json}')
        if articles_info.get('enabled'):
            print(f"[OK] Artigos sem sermão: {articles_info.get('pending', 0)} de {articles_info.get('total_artigos', 0)}")
        if articles_info.get('workspace_enabled'):
            print(f"[OK] Workspace Artigos: grupos={articles_info.get('workspace_groups', 0)}")
        for warning in articles_info.get('warnings', []):
            print(f'[WARN] {warning}')

    if args.browse or args.open_browse:
        browse_meta = {
            'input_dir_sermoes': str(input_dir),
            'input_dir_artigos': str(input_dir_artigos or ''),
            'workspace_artigos': str(workspace_artigos or ''),
        }
        generate_browse_html(sermon_rows_dict, browse_html, article_rows=article_rows, browse_meta=browse_meta)
        print(f'[OK] Browse gerado: {browse_html}')
        if args.open_browse:
            open_file(browse_html)

    if args.scan_only and not args.execute and not args.dry_run:
        return 0

    if args.execute or args.dry_run:
        selected = filter_rows(sermon_rows_dict, args)
        print(f'[INFO] Selecionados: {len(selected)}')
        if not selected:
            print('[INFO] Nenhum item selecionado pelos filtros informados.')
            return 0
        updated_rows, summary = execute_rows(selected, args, log_file, report_csv)
        updated_map = {row['id_base']: row for row in updated_rows}
        final_rows = []
        for d in sermon_rows_dict:
            if d['id_base'] in updated_map:
                d.update(updated_map[d['id_base']])
            final_rows.append(d)
        write_rows_json(final_rows, manifest_json)
        write_rows_csv(final_rows, manifest_csv)
        print('[OK] Execução concluída')
        print(f'[OK] Log: {log_file}')
        print(f'[OK] Relatório: {report_csv}')
        print(f"[OK] Novos: {summary['ok_new']} | Atualizados: {summary['ok_updated']} | Pulados: {summary['skip']} | Erros: {summary['error']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
