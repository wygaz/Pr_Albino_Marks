#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

TEXT_EXTS = {
    '.py', '.ps1', '.psm1', '.cmd', '.bat', '.sh', '.md', '.txt', '.json', '.yaml', '.yml',
    '.toml', '.ini', '.cfg', '.sql', '.html', '.css', '.js', '.ts', '.tsx', '.jsx', '.vba',
    '.vbs', '.rb', '.php', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.cs', '.r',
    '.lua', '.pl', '.xml'
}

EXCLUDE_DIRS = {
    '.git', '.venv', 'venv', '__pycache__', '.mypy_cache', '.pytest_cache', '.ruff_cache',
    'node_modules', '.idea', '.vscode', '_inventario_duplicatas'
}

TRACKED_CACHE: dict[Path, bool] = {}
MODIFIED_CACHE: dict[Path, bool] = {}


@dataclass
class FileInfo:
    name: str
    relpath: str
    abspath: Path
    size: int
    mtime: float
    sha256: str
    tracked_git: bool
    modified_git: bool
    class_suggested: str
    canonical_score: int
    notes: str


@dataclass
class GroupDecision:
    name: str
    status: str
    canonical_relpath: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def should_scan(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return False
    return True


def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob('*'):
        if p.is_file() and should_scan(p):
            yield p


def git_root(path: Path) -> Path | None:
    try:
        out = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(out.stdout.strip())
    except Exception:
        return None


def git_tracked(gitroot: Path | None, path: Path) -> bool:
    if gitroot is None:
        return False
    if path in TRACKED_CACHE:
        return TRACKED_CACHE[path]
    try:
        rel = path.relative_to(gitroot).as_posix()
        out = subprocess.run(
            ['git', 'ls-files', '--error-unmatch', rel],
            cwd=gitroot,
            capture_output=True,
            text=True,
        )
        ok = out.returncode == 0
    except Exception:
        ok = False
    TRACKED_CACHE[path] = ok
    return ok


def git_modified(gitroot: Path | None, path: Path) -> bool:
    if gitroot is None:
        return False
    if path in MODIFIED_CACHE:
        return MODIFIED_CACHE[path]
    try:
        rel = path.relative_to(gitroot).as_posix()
        out = subprocess.run(
            ['git', 'status', '--porcelain', '--', rel],
            cwd=gitroot,
            capture_output=True,
            text=True,
            check=False,
        )
        ok = bool(out.stdout.strip())
    except Exception:
        ok = False
    MODIFIED_CACHE[path] = ok
    return ok


def classify(relpath: str) -> tuple[str, str]:
    rp = relpath.replace('\\', '/').lower()
    notes: list[str] = []

    if '/migrations/' in rp or rp.endswith('/manage.py') or '/settings.py' in rp or '/urls.py' in rp or '/models.py' in rp or '/views.py' in rp or '/admin.py' in rp or '/forms.py' in rp:
        return 'codigo_app_fora_escopo', 'Código Django/app; não tratar como script operacional'

    if any(x in rp for x in ['pralbino', 'sermao', 'sermoes', 'artigo', 'artigos', 'esboco', 'esbocos', 'series_classificadas', 'series/']):
        notes.append('Conhece taxonomia/fluxo do Pr. Albino')
        return 'pr_albino_marks', '; '.join(notes)

    if any(x in rp for x in ['vocacional', 'sonhe', 'projeto21', 'escola_no_ar', 'cursos/']):
        notes.append('Relacionamento com Escola no Ar/guarda-chuva')
        return 'escola_no_ar', '; '.join(notes)

    if any(x in rp for x in ['/shared/', '/utils/', '/diagnostics/', 'certificados', 'macro_', 'zip_repo', 'check_secrets', 'rastrear_saneiar', 'inventariar_']):
        notes.append('Utilitário genérico / diagnóstico')
        return 'shared_generic', '; '.join(notes)

    if any(x in rp for x in ['_temp_update', '(1)', 'old', 'backup', 'copia', 'copy', '/zip/']):
        notes.append('Snapshot/cópia/backup')
        return 'revisar', '; '.join(notes)

    return 'revisar', 'Ambíguo; revisar manualmente'


def score_candidate(info: FileInfo) -> int:
    rp = info.relpath.replace('\\', '/').lower()
    score = 0

    if info.tracked_git:
        score += 50
    if info.modified_git:
        score += 10

    good_paths = [
        'tools/pralbino_pipeline/',
        'tools/pralbino_sermoes/',
        'scripts/publicacao/',
        'scripts/',
    ]
    bad_paths = [
        '/_temp_update/',
        '/zip/',
        '/backup',
        '/old',
        '(1)',
        '_sanitizados_preview',
        '_pacotes_chatgpt',
        '_diagnosticos_',
        '_inventario_'
    ]

    if any(g in rp for g in good_paths):
        score += 35
    if 'apenas_local' in rp:
        score -= 5
    if any(b in rp for b in bad_paths):
        score -= 40
    if '/revisar/' in rp:
        score -= 10

    if any(k in info.name.lower() for k in ['final', 'completo', 'pipeline', 'v2', 'v3']):
        score += 8

    # desempates leves
    score += min(int(info.size / 1000), 15)
    score += int(info.mtime // 86400) % 7
    return score


def build_inventory(root: Path, only_divergent: bool) -> tuple[list[FileInfo], dict[str, GroupDecision]]:
    gitroot = git_root(root)
    groups: dict[str, list[FileInfo]] = defaultdict(list)

    for path in iter_files(root):
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        rel = path.relative_to(root).as_posix()
        st = path.stat()
        cls, notes = classify(rel)
        info = FileInfo(
            name=path.name,
            relpath=rel,
            abspath=path,
            size=st.st_size,
            mtime=st.st_mtime,
            sha256=sha256_file(path),
            tracked_git=git_tracked(gitroot, path),
            modified_git=git_modified(gitroot, path),
            class_suggested=cls,
            canonical_score=0,
            notes=notes,
        )
        info.canonical_score = score_candidate(info)
        groups[info.name].append(info)

    rows: list[FileInfo] = []
    decisions: dict[str, GroupDecision] = {}

    for name, items in sorted(groups.items()):
        if len(items) < 2:
            continue
        hashes = {x.sha256 for x in items}
        status = 'identico' if len(hashes) == 1 else 'divergente'
        if only_divergent and status != 'divergente':
            continue
        winner = sorted(items, key=lambda x: (x.canonical_score, x.tracked_git, x.modified_git, x.mtime, x.size), reverse=True)[0]
        decisions[name] = GroupDecision(name=name, status=status, canonical_relpath=winner.relpath)
        rows.extend(sorted(items, key=lambda x: (x.name.lower(), x.relpath.lower())))

    return rows, decisions


def write_outputs(root: Path, rows: list[FileInfo], decisions: dict[str, GroupDecision]) -> Path:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    outdir = root / '_inventario_duplicatas' / ts
    outdir.mkdir(parents=True, exist_ok=True)

    csv_path = outdir / 'inventario_duplicatas.csv'
    md_path = outdir / 'inventario_duplicatas.md'

    with csv_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([
            'nome', 'status_grupo', 'candidato_canonico', 'relpath', 'sha256', 'size',
            'mtime_iso', 'tracked_git', 'modified_git', 'class_suggested', 'canonical_score', 'notes'
        ])
        for r in rows:
            d = decisions[r.name]
            w.writerow([
                r.name, d.status, d.canonical_relpath, r.relpath, r.sha256,
                r.size, datetime.fromtimestamp(r.mtime).isoformat(sep=' ', timespec='seconds'),
                r.tracked_git, r.modified_git, r.class_suggested, r.canonical_score, r.notes
            ])

    grouped: dict[str, list[FileInfo]] = defaultdict(list)
    for r in rows:
        grouped[r.name].append(r)

    with md_path.open('w', encoding='utf-8') as f:
        total_groups = len(grouped)
        divergent = sum(1 for g in grouped if decisions[g].status == 'divergente')
        identical = total_groups - divergent
        f.write('# Inventário controlado de duplicatas\n\n')
        f.write(f'- Grupos analisados: **{total_groups}**\n')
        f.write(f'- Divergentes: **{divergent}**\n')
        f.write(f'- Idênticos: **{identical}**\n\n')
        for name, items in sorted(grouped.items()):
            d = decisions[name]
            f.write(f'## {name}\n\n')
            f.write(f'- status: **{d.status}**\n')
            f.write(f'- candidato canônico: `{d.canonical_relpath}`\n\n')
            f.write('| relpath | sha256 (12) | tam | modificação | git | classe | score | notas |\n')
            f.write('|---|---|---:|---|---|---|---:|---|\n')
            for r in sorted(items, key=lambda x: (x.canonical_score, x.tracked_git, x.modified_git, x.mtime, x.size), reverse=True):
                git_state = ('T' if r.tracked_git else '-') + ('M' if r.modified_git else '-')
                mtime = datetime.fromtimestamp(r.mtime).strftime('%Y-%m-%d %H:%M:%S')
                f.write(f'| `{r.relpath}` | `{r.sha256[:12]}` | {r.size} | {mtime} | {git_state} | {r.class_suggested} | {r.canonical_score} | {r.notes} |\n')
            f.write('\n')

    return outdir


def main() -> None:
    ap = argparse.ArgumentParser(description='Inventaria duplicatas por nome de arquivo, com hash, datas e sugestão canônica.')
    ap.add_argument('--root', default='.', help='Raiz do projeto')
    ap.add_argument('--only-divergent', action='store_true', help='Mostra apenas grupos com mesmo nome e conteúdo diferente')
    args = ap.parse_args()

    root = Path(args.root).resolve()
    rows, decisions = build_inventory(root, args.only_divergent)
    outdir = write_outputs(root, rows, decisions)

    print('=== Inventário de duplicatas concluído ===')
    print(f'Raiz: {root}')
    print(f'Grupos encontrados: {len(decisions)}')
    print(f'Relatório CSV: {outdir / "inventario_duplicatas.csv"}')
    print(f'Relatório MD:  {outdir / "inventario_duplicatas.md"}')


if __name__ == '__main__':
    main()
