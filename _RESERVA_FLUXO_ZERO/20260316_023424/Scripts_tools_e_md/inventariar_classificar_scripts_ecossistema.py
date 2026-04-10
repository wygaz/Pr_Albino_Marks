from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

SCRIPT_EXTS = {'.py', '.ps1', '.bat', '.cmd', '.sh'}
DOC_EXTS = {'.md', '.txt', '.docx', '.pdf'}
CODE_OR_DOC_EXTS = SCRIPT_EXTS | DOC_EXTS
IGNORE_DIRS = {
    '.git', '.venv', 'venv', '__pycache__', 'node_modules', '.mypy_cache', '.pytest_cache',
    '_pacotes_chatgpt', '_diagnosticos_segredos', '_sanitizados_preview', '.idea', '.vscode'
}

GENERIC_KEYWORDS = [
    'zip', 'backup', 'rename', 'renome', 'listar', 'limpar', 'limpa', 'check', 'secret',
    'diag', 'diagnost', 'certificado', 'pdfmenu', 'converter_pdf_para_jpg', 'mover-data-pro-fim',
]

PRALBINO_KEYWORDS = [
    'pralbino', 'albino', 'sermao', 'sermoes', 'esboco', 'artigo', 'artigos', 'serie', 'series',
    'slug', 'publicar', 'importar_um_artigo', 'gerar_pdfs', 'gerar_imagens_lote',
]

ESCOLA_NO_AR_KEYWORDS = [
    'escola_no_ar', 'escola no ar', 'vocacional', 'vocacao', 'sonhe', 'alto',
    'projeto21', 'projeto_21', 'curso', 'cursos'
]

SITE_GAZETA_KEYWORDS = ['gazeta', 'sitio', 'sítio', 'portfolio', 'portifolio', 'portfolio']

@dataclass
class Row:
    relpath: str
    kind: str
    scope: str
    confidence: str
    suggested_target: str
    reason: str


def norm(s: str) -> str:
    return s.lower().replace('-', '_').replace(' ', '_')


def contains_any(text: str, words: Iterable[str]) -> list[str]:
    hits = []
    t = norm(text)
    for w in words:
        if norm(w) in t:
            hits.append(w)
    return hits


def classify(path: Path) -> Row:
    rel = path.as_posix()
    lname = norm(path.name)
    lpath = norm(rel)
    suffix = path.suffix.lower()

    kind = 'script' if suffix in SCRIPT_EXTS else 'doc_or_asset'
    scope = 'revisar'
    confidence = 'baixa'
    reason_parts: list[str] = []
    suggested_target = 'scripts/revisar'

    # explicit path signals first
    if 'diagnosticos' in lpath:
        scope = 'shared_diagnostics'
        confidence = 'alta'
        suggested_target = 'scripts/shared/diagnostics'
        reason_parts.append('está em pasta Diagnosticos')
    elif 'certificados' in lpath:
        scope = 'shared_infra'
        confidence = 'alta'
        suggested_target = 'scripts/shared/infra/certificados'
        reason_parts.append('material de certificado/infra')
    elif 'macro_' in lname or 'vba' in lname:
        scope = 'shared_docs_word'
        confidence = 'alta'
        suggested_target = 'scripts/shared/office_macros'
        reason_parts.append('macro/documentação Office')

    # keyword-based scope
    hits_pr = contains_any(lpath, PRALBINO_KEYWORDS)
    hits_ena = contains_any(lpath, ESCOLA_NO_AR_KEYWORDS)
    hits_gz = contains_any(lpath, SITE_GAZETA_KEYWORDS)
    hits_generic = contains_any(lpath, GENERIC_KEYWORDS)

    if scope == 'revisar':
        if hits_pr and not hits_ena and not hits_gz:
            scope = 'pr_albino_marks'
            confidence = 'alta' if len(hits_pr) >= 2 else 'média'
            suggested_target = 'scripts/apps/pr_albino_marks'
            reason_parts.append('palavras-chave Pr. Albino: ' + ', '.join(sorted(set(hits_pr))[:5]))
        elif hits_ena and not hits_pr and not hits_gz:
            scope = 'escola_no_ar'
            confidence = 'alta' if len(hits_ena) >= 2 else 'média'
            suggested_target = 'scripts/apps/escola_no_ar'
            reason_parts.append('palavras-chave Escola no Ar: ' + ', '.join(sorted(set(hits_ena))[:5]))
        elif hits_gz and not hits_pr and not hits_ena:
            scope = 'site_independente'
            confidence = 'média'
            suggested_target = 'scripts/apps/site_independente'
            reason_parts.append('palavras-chave site independente: ' + ', '.join(sorted(set(hits_gz))[:5]))
        elif hits_generic and not hits_pr and not hits_ena and not hits_gz:
            scope = 'shared_generic'
            confidence = 'média'
            suggested_target = 'scripts/shared/utils'
            reason_parts.append('palavras-chave genéricas: ' + ', '.join(sorted(set(hits_generic))[:5]))
        elif hits_pr and hits_ena:
            scope = 'revisar_multiapp'
            confidence = 'média'
            suggested_target = 'scripts/revisar/multiapp'
            reason_parts.append('mistura sinais Pr. Albino + Escola no Ar')
        else:
            # heuristics by path/name patterns
            if re.search(r'(import|export|convert|normalizar|consolidar|publicar|baixar|gerar)', lname):
                scope = 'shared_candidate'
                confidence = 'baixa'
                suggested_target = 'scripts/revisar/shared_candidate'
                reason_parts.append('verbo utilitário, mas sem app claro')
            else:
                scope = 'revisar'
                confidence = 'baixa'
                suggested_target = 'scripts/revisar'
                reason_parts.append('sem sinal suficiente')

    # refine target subareas for Pr Albino
    if scope == 'pr_albino_marks':
        if re.search(r'baixar_anexos|referenciad', lname):
            suggested_target = 'scripts/apps/pr_albino_marks/01_coleta'
        elif re.search(r'normalizar|classificar|consolidar|esboco|serie', lname):
            suggested_target = 'scripts/apps/pr_albino_marks/02_workspace'
        elif re.search(r'gerar_sermao|converter_em_pdf|gerar_pdfs|pdf', lname):
            suggested_target = 'scripts/apps/pr_albino_marks/03_producao'
        elif re.search(r'publicar|importar|slug|views|templates|urls', lname):
            suggested_target = 'scripts/apps/pr_albino_marks/04_publicacao'
        elif re.search(r'auditar|check|consistencia|comparar|listar', lname):
            suggested_target = 'scripts/apps/pr_albino_marks/90_diagnosticos'

    # Docs should often live alongside scripts/docs
    if kind == 'doc_or_asset':
        if 'instrucoes' in lname or 'manual' in lname or suffix in {'.md', '.txt', '.docx', '.pdf'}:
            suggested_target = suggested_target.replace('scripts/', 'docs/scripts/')

    return Row(
        relpath=rel,
        kind=kind,
        scope=scope,
        confidence=confidence,
        suggested_target=suggested_target,
        reason='; '.join(reason_parts),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description='Inventaria e classifica scripts/documentação operacional do ecossistema.')
    ap.add_argument('--root', default='.', help='Raiz a escanear')
    ap.add_argument('--outdir', default='_inventario_scripts', help='Pasta base de saída')
    ap.add_argument('--include-docs', action='store_true', help='Inclui docs operacionais (.md/.txt/.docx/.pdf)')
    args = ap.parse_args()

    root = Path(args.root).resolve()
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    outdir = root / args.outdir / stamp
    outdir.mkdir(parents=True, exist_ok=True)

    rows: list[Row] = []
    allowed = CODE_OR_DOC_EXTS if args.include_docs else SCRIPT_EXTS

    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix.lower() not in allowed:
            continue
        parts = set(path.parts)
        if parts & IGNORE_DIRS:
            continue
        rows.append(classify(path.relative_to(root)))

    rows.sort(key=lambda r: (r.scope, r.relpath))

    csv_path = outdir / 'inventario_scripts.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['relpath', 'kind', 'scope', 'confidence', 'suggested_target', 'reason'])
        for r in rows:
            w.writerow([r.relpath, r.kind, r.scope, r.confidence, r.suggested_target, r.reason])

    summary: dict[str, int] = {}
    for r in rows:
        summary[r.scope] = summary.get(r.scope, 0) + 1

    md_path = outdir / 'inventario_scripts.md'
    with md_path.open('w', encoding='utf-8') as f:
        f.write('# Inventário de scripts\n\n')
        f.write(f'Raiz: `{root}`\n\n')
        f.write(f'Total: **{len(rows)}**\n\n')
        f.write('## Resumo por escopo\n\n')
        for scope, count in sorted(summary.items(), key=lambda kv: (-kv[1], kv[0])):
            f.write(f'- **{scope}**: {count}\n')
        f.write('\n## Itens\n\n')
        current = None
        for r in rows:
            if r.scope != current:
                current = r.scope
                f.write(f'### {current}\n\n')
            f.write(f'- `{r.relpath}` → `{r.suggested_target}` [{r.confidence}]')
            if r.reason:
                f.write(f' — {r.reason}')
            f.write('\n')

    print('=== Inventário concluído ===')
    print(f'Raiz: {root}')
    print(f'Itens classificados: {len(rows)}')
    print(f'CSV: {csv_path}')
    print(f'MD:  {md_path}')


if __name__ == '__main__':
    main()
