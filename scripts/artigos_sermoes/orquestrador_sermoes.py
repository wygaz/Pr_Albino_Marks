from __future__ import annotations

import argparse
import csv
import json
import os
import re
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
    parser = argparse.ArgumentParser(description='Orquestrador de sermÃµes â€” Etapa 2')
    parser.add_argument('--root', default='.')
    parser.add_argument('--input-dir', required=True, help='Pasta dos sermÃµes formatados')
    parser.add_argument('--input-dir-artigos', help='Pasta-base dos artigos/insumos para geraÃ§Ã£o de sermÃ£o')
    parser.add_argument('--workspace-artigos', help='Workspace operacional dos artigos (opcional; default = input-dir-artigos)')
    parser.add_argument('--manifest-csv')
    parser.add_argument('--manifest-json')
    parser.add_argument('--manifest-overrides', help='CSV/JSON com metadados corrigidos por id_base (titulo, serie, autor, slug_previsto etc.)')
    parser.add_argument('--manifest-overrides-template', help='CSV gerado automaticamente para preenchimento manual de metadados')
    parser.add_argument('--articles-manifest-csv')
    parser.add_argument('--articles-manifest-json')
    parser.add_argument('--browse-html')
    parser.add_argument('--selection-file')
    parser.add_argument('--steps', help='Etapas canÃ´nicas. Ex.: 1,2 | 6-9 | 10')
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
    parser.add_argument('--python-exe', help='Default: <root>\\venv\\Scripts\\python.exe')
    parser.add_argument('--extract-script', help='Default: deposito_geral/extracao_de_artigos.py')
    parser.add_argument('--prepare-script', help='Default: deposito_geral/preparacao_do_ambiente_operacional.py')
    parser.add_argument('--prompts-script', help='Default: deposito_geral/gerar_prompts_imagens_operacional.py')
    parser.add_argument('--images-script', help='Default: deposito_geral/gerar_imagens_lote_operacional.py')
    parser.add_argument('--pdfs-script', help='Default: deposito_geral/gerar_pdfs_artigos_operacional.py')
    parser.add_argument('--publish-articles-script', help='Default: deposito_geral/publicar_artigos_operacional.py')
    parser.add_argument('--report-script', help='Default: script local de gerar_relatorio_tecnico_de_docx.py')
    parser.add_argument('--report-export-script', help='Default: script local de exportar_formatos_relatorio_md.py')
    parser.add_argument('--sermon-script', help='Default: script local de gerar_sermao_de_relatorio.py')
    parser.add_argument('--export-script', help='Default: script local de exportar_formatos_sermao_md.py')
    parser.add_argument('--publish-sermon-script', help='Default: deposito_geral/pipeline_publicar_sermao.py')
    parser.add_argument('--pipeline-script', help='Default: deposito_geral/run_pipeline_sermao_completo.ps1')
    parser.add_argument('--extract-ini', help='Default do script de extraÃ§Ã£o')
    parser.add_argument('--extract-fim', help='Default do script de extraÃ§Ã£o')
    parser.add_argument('--extract-ini-complementar')
    parser.add_argument('--extract-fim-complementar')
    parser.add_argument('--baixar-esbocos', action='store_true')
    parser.add_argument('--artigos-lote', help='Default: lote mais recente em Apenas_Local/anexos_filtrados')
    parser.add_argument('--esboco-path', help='Default: Apenas_Local/anexos_filtrados/Docs/ESBOCO_Geral_Series_1_a_4.docx')
    parser.add_argument('--artigos-workspace-input', help='Default: Apenas_Local/anexos_filtrados/<lote>/_entrada_preparacao')
    parser.add_argument('--operacional-output', help='Default: Apenas_Local/anexos_filtrados/<lote>/ambiente_operacional')
    parser.add_argument('--series-root', help='Default: Apenas_Local/operacional/artigos/series')
    parser.add_argument('--prompts-csv', help='Default: prefere Apenas_Local/operacional/artigos/prompts_imagem/pr_albino_prompts_ricos_58_artigos.csv e cai para prompts_imagens_operacional.csv')
    parser.add_argument('--images-root', help='Default: Apenas_Local/operacional/artigos/imagens')
    parser.add_argument('--pdfs-root', help='Default: Apenas_Local/operacional/artigos/pdfs')
    parser.add_argument('--reports-root', help='Default: Apenas_Local/operacional/dossies/markdown')
    parser.add_argument('--dossies-formatados-root', help='Default: Apenas_Local/operacional/dossies/formatados')
    parser.add_argument('--sermoes-md-root', help='Default: Apenas_Local/operacional/sermoes/markdown')
    parser.add_argument('--sermoes-formatados-root', help='Default: Apenas_Local/operacional/sermoes/formatados')
    parser.add_argument('--sermao-model', default='gpt-5')
    parser.add_argument('--overwrite-images', action='store_true')
    parser.add_argument('--overwrite-pdfs', action='store_true')
    parser.add_argument('--overwrite-media', action='store_true')
    parser.add_argument('--publish-kind', choices=['all', 'docx', 'pdf', 'img'], help='Tipo de publicação para o step 6')
    parser.add_argument('--execute-context', help='Default: inferido do JSON do browse')
    parser.add_argument('--django-settings', help='Ex.: pralbinomarks.settings')
    parser.add_argument('--no-db-hydrate', action='store_true', help='Desliga a hidrataÃ§Ã£o do manifest pelo BD Django')
    parser.add_argument('--no-articles-context', action='store_true', help='NÃ£o gera o contexto Artigos sem sermÃ£o no browse')
    return parser.parse_args()


def default_paths(root: Path) -> dict:
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = root / 'Apenas_Local'
    homologacao = base / 'scripts' / 'homologacao'
    return {
        'manifest_csv': homologacao / 'manifest_sermoes.csv',
        'manifest_json': homologacao / 'manifest_sermoes.json',
        'manifest_overrides': homologacao / 'manifest_sermoes_overrides.csv',
        'manifest_overrides_template': homologacao / 'manifest_sermoes_overrides_modelo.csv',
        'articles_manifest_csv': homologacao / 'manifest_artigos_sem_sermao.csv',
        'articles_manifest_json': homologacao / 'manifest_artigos_sem_sermao.json',
        'browse_html': homologacao / 'manifest_sermoes.html',
        'log_file': homologacao / f'publicacao_sermoes_lote_{stamp}.log',
        'report_csv': homologacao / f'relatorio_lote_{stamp}.csv',
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


def infer_selection_context(selection_file: str | None) -> str:
    if not selection_file:
        return 'sermoes_formatados'
    try:
        payload = json.loads(Path(selection_file).read_text(encoding='utf-8'))
        return str(payload.get('current_context') or 'sermoes_formatados')
    except Exception:
        return 'sermoes_formatados'


def infer_latest_lote(base_dir: Path) -> str:
    candidates: list[str] = []
    if base_dir.exists():
        for child in base_dir.iterdir():
            if not child.is_dir():
                continue
            name = child.name.strip()
            if name.lower() == 'docs':
                continue
            if len(name) == 10 and name[4] == '_' and name[7] == '_':
                y, m, d = name.split('_')
                if y.isdigit() and m.isdigit() and d.isdigit():
                    candidates.append(name)
    if not candidates:
        return '2026_03_29'
    return sorted(candidates)[-1]


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


def batch_feedback(rows: list[dict]) -> list[str]:
    feedback: list[str] = []
    for row in rows:
        id_base = str(row.get('id_base', '') or '')
        if not id_base.startswith('batch_step_'):
            continue
        title = str(row.get('titulo', '') or '')
        msg = str(row.get('mensagem', '') or '')
        if not msg:
            continue
        ok_count = len(re.findall(r'^\s*\[OK\]\s', msg, flags=re.M))
        skip_count = len(re.findall(r'^\s*\[SKIP\]\s', msg, flags=re.M))
        err_count = len(re.findall(r'^\s*\[ERRO\]\s', msg, flags=re.M))
        if 'Batch step 4' in title:
            paths = re.findall(r'^\s*\[OK\]\s+(.+\.png)\s*$', msg, flags=re.M)
            feedback.append(f'[OK] Imagens geradas: {ok_count} | Puladas: {skip_count} | Erros: {err_count}')
            if paths:
                feedback.append(f'[OK] Pasta de saida: {Path(paths[-1]).parent}')
        elif 'Batch step 5' in title:
            paths = re.findall(r'^\s*\[(?:OK|SKIP)\]\s+(.+\.pdf)\s*$', msg, flags=re.M)
            feedback.append(f'[OK] PDFs gerados: {ok_count} | Pulados: {skip_count} | Erros: {err_count}')
            if paths:
                feedback.append(f'[OK] Pasta de saida: {Path(paths[-1]).parent}')
    return feedback


def refresh_manifests_and_browse(
    *,
    root: Path,
    input_dir: Path,
    input_dir_artigos: Path | None,
    workspace_artigos: Path | None,
    manifest_csv: Path,
    manifest_json: Path,
    overrides_path: Path,
    overrides_template_path: Path,
    articles_manifest_csv: Path,
    articles_manifest_json: Path,
    browse_html: Path,
    django_settings: str | None,
    no_db_hydrate: bool,
    no_articles_context: bool,
) -> dict:
    previous = load_previous_manifest(manifest_json if manifest_json.exists() else manifest_csv)
    overrides = load_overrides(overrides_path)
    rows = scan_sermons(input_dir, previous=previous, overrides=overrides)

    db_info = {'enabled': False, 'warnings': []}
    if not no_db_hydrate:
        db_info = hydrate_rows_from_django(rows, root=root, settings_module=django_settings)
        for row in rows:
            prev_signature = previous.get(row.id_base, {}).get('assinatura_entrada', '')
            refresh_row_state(row, prev_signature=str(prev_signature or ''))

    write_manifest_csv(rows, manifest_csv)
    write_manifest_json(rows, manifest_json)
    write_overrides_template_csv(rows, overrides_template_path)
    sermon_rows_dict = [r.to_dict() for r in rows]

    article_rows: list[dict] = []
    articles_info = {'enabled': False, 'warnings': []}
    if not no_articles_context and not no_db_hydrate:
        article_rows, articles_info = fetch_articles_without_sermon(
            root=root,
            settings_module=django_settings,
            sermon_rows=sermon_rows_dict,
            input_dir_artigos=input_dir_artigos,
            workspace_artigos=workspace_artigos,
        )
        write_rows_csv(article_rows, articles_manifest_csv)
        write_rows_json(article_rows, articles_manifest_json)

    browse_meta = {
        'input_dir_sermoes': str(input_dir),
        'input_dir_artigos': str(input_dir_artigos or ''),
        'workspace_artigos': str(workspace_artigos or ''),
    }
    generate_browse_html(sermon_rows_dict, browse_html, article_rows=article_rows, browse_meta=browse_meta)
    return {
        'sermon_rows': sermon_rows_dict,
        'article_rows': article_rows,
        'db_info': db_info,
        'articles_info': articles_info,
    }


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    scripts_dir = Path(__file__).resolve().parent
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
    anexos_root = root / 'Apenas_Local' / 'anexos_filtrados'
    args.artigos_lote = args.artigos_lote or infer_latest_lote(anexos_root)
    lote_dir = anexos_root / args.artigos_lote
    args.python_exe = args.python_exe or str(root / 'venv' / 'Scripts' / 'python.exe')
    args.extract_script = args.extract_script or str(scripts_dir / 'extracao_de_artigos.py')
    args.prepare_script = args.prepare_script or str(scripts_dir / 'preparacao_do_ambiente_operacional.py')
    args.prompts_script = args.prompts_script or str(scripts_dir / 'gerar_prompts_imagens_operacional.py')
    args.images_script = args.images_script or str(scripts_dir / 'gerar_imagens_lote_operacional.py')
    args.pdfs_script = args.pdfs_script or str(scripts_dir / 'gerar_pdfs_artigos_operacional.py')
    args.publish_articles_script = args.publish_articles_script or str(scripts_dir / 'publicar_artigos_operacional.py')
    args.report_script = args.report_script or str(scripts_dir / 'gerar_relatorio_tecnico_de_docx.py')
    args.report_export_script = args.report_export_script or str(scripts_dir / 'exportar_formatos_relatorio_md.py')
    args.sermon_script = args.sermon_script or str(scripts_dir / 'gerar_sermao_de_relatorio.py')
    args.export_script = args.export_script or str(scripts_dir / 'exportar_formatos_sermao_md.py')
    args.publish_sermon_script = args.publish_sermon_script or str(scripts_dir / 'pipeline_publicar_sermao.py')
    args.pipeline_script = args.pipeline_script or str(scripts_dir / 'run_pipeline_sermao_completo.ps1')
    args.esboco_path = args.esboco_path or str(root / 'Apenas_Local' / 'anexos_filtrados' / 'Docs' / 'ESBOCO_Geral_Series_1_a_4.docx')
    args.artigos_workspace_input = args.artigos_workspace_input or str(lote_dir / '_entrada_preparacao')
    args.operacional_output = args.operacional_output or str(lote_dir / 'ambiente_operacional')
    args.series_root = args.series_root or str(root / 'Apenas_Local' / 'operacional' / 'artigos' / 'series')
    if not args.prompts_csv:
        prompts_root = root / 'Apenas_Local' / 'operacional' / 'artigos' / 'prompts_imagem'
        preferred_prompts = prompts_root / 'pr_albino_prompts_ricos_58_artigos.csv'
        fallback_prompts = prompts_root / 'prompts_imagens_operacional.csv'
        args.prompts_csv = str(preferred_prompts if preferred_prompts.exists() else fallback_prompts)
    args.images_root = args.images_root or str(root / 'Apenas_Local' / 'operacional' / 'artigos' / 'imagens')
    args.pdfs_root = args.pdfs_root or str(root / 'Apenas_Local' / 'operacional' / 'artigos' / 'pdfs')
    args.reports_root = args.reports_root or str(root / 'Apenas_Local' / 'operacional' / 'dossies' / 'markdown')
    args.dossies_formatados_root = args.dossies_formatados_root or str(root / 'Apenas_Local' / 'operacional' / 'dossies' / 'formatados')
    args.sermoes_md_root = args.sermoes_md_root or str(root / 'Apenas_Local' / 'operacional' / 'sermoes' / 'markdown')
    args.sermoes_formatados_root = args.sermoes_formatados_root or str(root / 'Apenas_Local' / 'operacional' / 'sermoes' / 'formatados')

    refreshed = refresh_manifests_and_browse(
        root=root,
        input_dir=input_dir,
        input_dir_artigos=input_dir_artigos,
        workspace_artigos=workspace_artigos,
        manifest_csv=manifest_csv,
        manifest_json=manifest_json,
        overrides_path=overrides_path,
        overrides_template_path=overrides_template_path,
        articles_manifest_csv=articles_manifest_csv,
        articles_manifest_json=articles_manifest_json,
        browse_html=browse_html,
        django_settings=args.django_settings,
        no_db_hydrate=args.no_db_hydrate,
        no_articles_context=args.no_articles_context,
    )
    sermon_rows_dict = refreshed['sermon_rows']
    db_info = refreshed['db_info']
    summary_scan = summarize_rows(sermon_rows_dict)

    print(f'[OK] InputDir SermÃµes: {input_dir}')
    if input_dir_artigos:
        print(f'[OK] InputDir Artigos: {input_dir_artigos}')
    if workspace_artigos:
        print(f'[OK] Workspace Artigos: {workspace_artigos}')
    print(f'[OK] Manifest CSV: {manifest_csv}')
    print(f'[OK] Manifest JSON: {manifest_json}')
    print(f'[OK] Modelo de overrides: {overrides_template_path}')
    print(f"[OK] Itens encontrados: {summary_scan['total']}")
    print(f"[OK] Completos: {summary_scan['completos']} | Publicados: {summary_scan['publicados']} | Alterados: {summary_scan['alterados']}")
    print(f"[OK] Sem sÃ©rie: {summary_scan['sem_serie']} | Sem autor: {summary_scan['sem_autor']} | Match BD: {summary_scan['com_match_bd']}")
    if overrides_path.exists():
        print(f'[OK] Overrides aplicados: {overrides_path}')
    else:
        print(f'[INFO] Overrides ainda nÃ£o encontrados. Preencha, se desejar: {overrides_path}')

    if db_info.get('enabled'):
        print(f"[OK] BD hidratado via {db_info.get('settings_module')} | match={db_info.get('matched', 0)} | sÃ©rie(area)={db_info.get('filled_serie', 0)} | autor={db_info.get('filled_autor', 0)}")
    for warning in db_info.get('warnings', []):
        print(f'[WARN] {warning}')

    article_rows: list[dict] = refreshed['article_rows']
    articles_info = refreshed['articles_info']
    if not args.no_articles_context and not args.no_db_hydrate:
        print(f'[OK] Manifest Artigos CSV: {articles_manifest_csv}')
        print(f'[OK] Manifest Artigos JSON: {articles_manifest_json}')
        if articles_info.get('enabled'):
            print(
                f"[OK] Artigos sem sermao / classificados: "
                f"{articles_info.get('pending', 0)} de {articles_info.get('total_artigos', 0)}"
            )
        if articles_info.get('workspace_enabled'):
            print(f"[OK] Workspace Artigos: grupos={articles_info.get('workspace_groups', 0)}")
        for warning in articles_info.get('warnings', []):
            print(f'[WARN] {warning}')

    if args.browse or args.open_browse:
        print(f'[OK] Browse gerado: {browse_html}')
        if args.open_browse:
            open_file(browse_html)

    if args.scan_only and not args.execute and not args.dry_run:
        return 0

    if args.execute or args.dry_run:
        args.execute_context = args.execute_context or infer_selection_context(args.selection_file)
        source_rows = article_rows if args.execute_context == 'artigos_sem_sermao' else sermon_rows_dict
        selected = filter_rows(source_rows, args)
        print(f'[INFO] Selecionados: {len(selected)}')
        if not selected:
            print('[INFO] Nenhum item selecionado pelos filtros informados.')
            return 0
        updated_rows, summary = execute_rows(selected, args, log_file, report_csv)
        updated_map = {row['id_base']: row for row in updated_rows}
        final_rows = []
        if args.execute_context == 'artigos_sem_sermao':
            for d in article_rows:
                if d['id_base'] in updated_map:
                    d.update(updated_map[d['id_base']])
                final_rows.append(d)
            write_rows_json(final_rows, articles_manifest_json)
            write_rows_csv(final_rows, articles_manifest_csv)
        else:
            for d in sermon_rows_dict:
                if d['id_base'] in updated_map:
                    d.update(updated_map[d['id_base']])
                final_rows.append(d)
            write_rows_json(final_rows, manifest_json)
            write_rows_csv(final_rows, manifest_csv)
        print('[OK] ExecuÃ§Ã£o concluÃ­da')
        print(f'[OK] Log: {log_file}')
        print(f'[OK] RelatÃ³rio: {report_csv}')
        print(f"[OK] Novos: {summary['ok_new']} | Atualizados: {summary['ok_updated']} | Pulados: {summary['skip']} | Erros: {summary['error']}")
        for line in batch_feedback(updated_rows):
            print(line)
        refreshed_after = refresh_manifests_and_browse(
            root=root,
            input_dir=input_dir,
            input_dir_artigos=input_dir_artigos,
            workspace_artigos=workspace_artigos,
            manifest_csv=manifest_csv,
            manifest_json=manifest_json,
            overrides_path=overrides_path,
            overrides_template_path=overrides_template_path,
            articles_manifest_csv=articles_manifest_csv,
            articles_manifest_json=articles_manifest_json,
            browse_html=browse_html,
            django_settings=args.django_settings,
            no_db_hydrate=args.no_db_hydrate,
            no_articles_context=args.no_articles_context,
        )
        print('[OK] Manifesto/Browse atualizados apos a execucao')
        if not args.no_articles_context and not args.no_db_hydrate:
            info = refreshed_after['articles_info']
            print(f"[OK] Artigos sem sermao / classificados: {info.get('pending', 0)} de {info.get('total_artigos', 0)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
