import argparse
import csv
import os
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

# =========================
# UTIL: localizar raiz do repo (manage.py/.git)
# =========================
def find_repo_root(start: Path, max_levels: int = 10) -> Path | None:
    cur = start
    for _ in range(max_levels + 1):
        if (cur / 'manage.py').exists() or (cur / '.git').exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def resolve_data_root(arg_value: str | None, scripts_dir: Path) -> Path:
    """
    Resolve a pasta 'anexos_filtrados' (DataRoot).
    - Se o usuário passou --data-root: usa ele
    - Senão: tenta <RepoRoot>/Apenas_Local/anexos_filtrados
    - Fallback: comportamento legado (scripts_dir.parent)
    """
    if arg_value and str(arg_value).strip():
        return Path(arg_value).expanduser().resolve()

    repo = find_repo_root(scripts_dir)
    if repo:
        cand = (repo / 'Apenas_Local' / 'anexos_filtrados')
        if cand.exists():
            return cand.resolve()

    return scripts_dir.parent.resolve()



def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def norm(s: str) -> str:
    s = strip_accents(s or "").lower()
    # normaliza espaços
    return " ".join(s.split())


def find_soffice() -> str:
    env = os.getenv("SOFFICE_PATH")
    if env and Path(env).exists():
        return env

    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    if shutil.which("soffice"):
        return "soffice"

    raise SystemExit(
        "Não encontrei o LibreOffice.\n"
        "Defina SOFFICE_PATH no .env.local, por ex:\n"
        "SOFFICE_PATH=C:\\Program Files\\LibreOffice\\program\\soffice.exe"
    )


def read_manifest_rows(path: Path):
    raw = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    raw = [l for l in raw if l.strip()]
    if not raw:
        return []

    first = raw[0].strip()
    # caso: "a;b;c"
    if first.startswith('"') and first.endswith('"') and ";" in first:
        def unq(s: str) -> str:
            s = s.strip()
            return s[1:-1] if s.startswith('"') and s.endswith('"') else s

        raw = [unq(l) for l in raw]
        header = raw[0].split(";")
        rows = []
        for line in raw[1:]:
            parts = line.split(";")
            if len(parts) < len(header):
                parts += [""] * (len(header) - len(parts))
            rows.append(dict(zip(header, parts[: len(header)])))
        return rows

    delim = ";" if ";" in raw[0] else ","
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delim))


def get_first(r: dict, *keys: str) -> str:
    for k in keys:
        v = r.get(k)
        if v is not None:
            v = str(v).strip()
            if v:
                return v
    return ""


def get_status(r: dict) -> str:
    return get_first(r, "status", "Status", "STATUS").strip().upper()


def convert_docx_to_pdf(soffice: str, docx: Path, out_dir: Path) -> None:
    cmd = [
        soffice,
        "--headless",
        "--nologo",
        "--nolockcheck",
        "--nodefault",
        "--nofirststartwizard",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(docx),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "").strip()[:800])


def resolve_series_dir(series_name: str | None, base_dir: Path, scripts_dir: Path) -> tuple[Path, str]:
    series_root = base_dir / 'SERIES'

    if not series_name:
        last = scripts_dir / '.last_series.txt'
        if last.exists():
            series_name = last.read_text(encoding='utf-8', errors='replace').strip()
        else:
            raise SystemExit('Informe --serie ou crie .last_series.txt')

    series_dir = series_root / series_name
    if not series_dir.exists():
        raise SystemExit(f'Série não encontrada: {series_dir}')

    return series_dir, series_name


def main():
    ap = argparse.ArgumentParser(description="Converte DOCX->PDF usando manifest.csv da SÉRIE (pipeline novo).")
    ap.add_argument("--serie", default="", help="Nome da série (SERIES/<SÉRIE>). Default: usa .last_series.txt")
    ap.add_argument("--overwrite", action="store_true", help="Sobrescreve PDFs existentes")
    ap.add_argument("--limit", type=int, default=0, help="Processa no máximo N itens (0=sem limite)")
    args = ap.parse_args()

    soffice = find_soffice()
    base_dir = resolve_data_root(args.data_root, scripts_dir)
    series_dir, series_name = resolve_series_dir(args.serie, base_dir=base_dir, scripts_dir=scripts_dir)

    manifest = series_dir / "manifest.csv"
    docx_dir = series_dir / "DOCX"
    out_dir = series_dir / "PDF"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not manifest.exists():
        raise SystemExit(f"manifest.csv não encontrado: {manifest}")
    if not docx_dir.exists():
        raise SystemExit(f"Pasta DOCX não encontrada: {docx_dir}")

    rows = read_manifest_rows(manifest)
    rows = [r for r in rows if get_status(r) == "OK"]

    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    # índice por stem normalizado (fallback)
    index = {}
    for p in docx_dir.glob("*.docx"):
        index[norm(p.stem)] = p

    print(f"Série: {series_name}")
    print("LibreOffice:", soffice)
    print(f"Itens OK no manifest: {len(rows)}")
    print(f"Saída PDFs: {out_dir}\n")

    ok = skip = fail = 0

    for i, r in enumerate(rows, start=1):
        titulo = get_first(r, "titulo_esboco", "titulo_normalizado", "titulo")
        docx_match = get_first(r, "docx_match", "docx")
        destino_docx = get_first(r, "destino_docx", "path_docx", "caminho_docx")

        docx_path = None
        if destino_docx:
            p = Path(destino_docx)
            if p.exists():
                docx_path = p
        if docx_path is None and docx_match:
            p = docx_dir / docx_match
            if p.exists():
                docx_path = p
        if docx_path is None and titulo:
            docx_path = index.get(norm(titulo))

        if docx_path is None or not docx_path.exists():
            print(f"[{i}/{len(rows)}] ❌ DOCX não encontrado: {titulo}")
            fail += 1
            continue

        pdf_path = out_dir / f"{docx_path.stem}.pdf"

        if pdf_path.exists() and not args.overwrite:
            print(f"[{i}/{len(rows)}] Pular (já existe): {pdf_path.name}")
            skip += 1
            continue

        print(f"[{i}/{len(rows)}] Convertendo: {docx_path.name}")
        try:
            convert_docx_to_pdf(soffice, docx_path, out_dir)
            ok += 1
        except Exception as e:
            print(f"    ❌ Falhou: {docx_path.name} -> {e}")
            fail += 1

    print(f"\n✅ Finalizado. OK: {ok} | Pulados: {skip} | Falhas: {fail}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\nERRO:", e)
        sys.exit(1)
