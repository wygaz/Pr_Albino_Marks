import re
import argparse
from pathlib import Path
from docx import Document

DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SM_RE = re.compile(r"^\s*sm\s*\d+\s*[-–—:]\s*|\s*^\s*sm\s*\d+\s*", re.IGNORECASE)
DATE_RE1 = re.compile(r"^\s*\d{4}-\d{2}-\d{2}\s*[-–—:]\s*")
DATE_RE2 = re.compile(r"^\s*\d{2}-\d{2}-\d{4}\s*[-–—:]\s*")
WS_RE = re.compile(r"\s+")
INVALID_WIN = re.compile(r'[<>:"/\\|?*]')

def clean_title(s: str) -> str:
    s = (s or "").strip()
    s = DATE_RE1.sub("", s)
    s = DATE_RE2.sub("", s)
    s = SM_RE.sub("", s)
    s = WS_RE.sub(" ", s).strip()
    return s

def safe_filename(name: str, max_len: int = 140) -> str:
    name = clean_title(name).upper()
    name = INVALID_WIN.sub("", name).strip().rstrip(".")
    name = WS_RE.sub(" ", name).strip()
    if not name:
        name = "SEM_TITULO"
    return name[:max_len] if len(name) > max_len else name

def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    base = path.with_suffix("")
    ext = path.suffix
    i = 2
    while True:
        cand = Path(f"{base}_{i}{ext}")
        if not cand.exists():
            return cand
        i += 1

def rename_force(src: Path, dst: Path) -> Path:
    """Renomeia mesmo quando só muda maiúsculas/minúsculas (Windows)."""
    if src.resolve() == dst.resolve():
        return src
    tmp = src.with_name(src.name + ".__tmp__")
    if tmp.exists():
        tmp = unique_path(tmp)
    src.rename(tmp)
    tmp.rename(dst)
    return dst

def best_doc_title(doc: Document) -> str:
    t = clean_title(doc.core_properties.title or "")
    if t:
        return t
    for p in doc.paragraphs:
        txt = clean_title(p.text or "")
        if txt:
            return txt
    return ""

def pick_latest_date_folder(base: Path) -> str | None:
    dates = []
    for d in base.iterdir():
        if d.is_dir() and DATE_DIR_RE.match(d.name):
            dates.append(d.name)
    return max(dates) if dates else None

def main():
    ap = argparse.ArgumentParser(description="Normaliza nomes e Title interno dos DOCX no lote (YYYY-MM-DD).")
    ap.add_argument("--lote", help="Nome da pasta do lote (YYYY-MM-DD). Se omitido, usa a mais recente.")
    args = ap.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    base = scripts_dir.parent  # ...\anexos_filtrados
    latest = pick_latest_date_folder(base)

    chosen = (args.lote or "").strip()
    if not chosen:
        print("\n📁 Base:", base)
        prompt = f"Data do lote (AAAA-MM-DD) [default: {latest or 'nenhuma'}]: "
        chosen = input(prompt).strip() or (latest or "")

    if not chosen:
        raise SystemExit("Não encontrei nenhuma pasta YYYY-MM-DD e você não informou uma data.")

    folder = base / chosen
    if not folder.exists():
        raise SystemExit(f"Pasta não encontrada: {folder}")

    docx_files = sorted(folder.glob("*.docx"))
    print(f"\n📄 DOCX em {folder.name}: {len(docx_files)}")

    for f in docx_files:
        doc = Document(str(f))
        title = safe_filename(best_doc_title(doc))

        doc.core_properties.title = title
        doc.save(str(f))

        new_docx = unique_path(f.with_name(f"{title}.docx"))
        if new_docx.name != f.name:
            new_docx = rename_force(f, new_docx)

        old_pdf = f.with_suffix(".pdf")
        if old_pdf.exists():
            new_pdf = unique_path(new_docx.with_suffix(".pdf"))
            if new_pdf.name != old_pdf.name:
                rename_force(old_pdf, new_pdf)

        print("✅", new_docx.name)

    print("\n✅ Normalização concluída.")

if __name__ == "__main__":
    main()
