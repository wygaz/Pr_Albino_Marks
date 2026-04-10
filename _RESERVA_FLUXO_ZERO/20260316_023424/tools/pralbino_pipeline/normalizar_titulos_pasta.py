import re
import argparse
import shutil
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
    - Fallback: scripts_dir.parent
    """
    if arg_value and str(arg_value).strip():
        return Path(arg_value).expanduser().resolve()

    repo = find_repo_root(scripts_dir)
    if repo:
        cand = (repo / 'Apenas_Local' / 'anexos_filtrados')
        if cand.exists():
            return cand.resolve()

    return scripts_dir.parent.resolve()


def copiar_para_docx_normalizados(base: Path, chosen: str, docx_paths: list[Path]) -> Path:
    """
    Copia (não move) os DOCX (e PDFs com mesmo stem) para:
    <base>/DOCX_NORMALIZADOS/<chosen>/
    """
    dest_dir = (base / "DOCX_NORMALIZADOS" / chosen)
    dest_dir.mkdir(parents=True, exist_ok=True)

    for src_docx in docx_paths:
        # copia docx
        dst_docx = unique_path(dest_dir / src_docx.name)
        shutil.copy2(src_docx, dst_docx)

        # copia pdf correspondente (se existir)
        src_pdf = src_docx.with_suffix(".pdf")
        if src_pdf.exists():
            dst_pdf = unique_path(dest_dir / src_pdf.name)
            shutil.copy2(src_pdf, dst_pdf)

    return dest_dir


def main():
    ap = argparse.ArgumentParser(description="Normaliza nomes e Title interno dos DOCX no lote (YYYY-MM-DD).")
    ap.add_argument("--data-root", default="", help="Pasta 'anexos_filtrados' (DataRoot). Se vazio, tenta repo/Apenas_Local/anexos_filtrados.")
    ap.add_argument("--lote", help="Nome da pasta do lote (YYYY-MM-DD). Se omitido, usa a mais recente.")
    ap.add_argument("--copiar-normalizados", action="store_true",
                    help="Após normalizar, copia DOCX/PDF para <base>/DOCX_NORMALIZADOS/<lote>/")
    ap.add_argument("--modo", choices=["publicacao", "sermoes", "nenhum"], default="nenhum",
                    help="Apenas imprime sugestão do próximo passo após normalizar.")
    args = ap.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    base = resolve_data_root(args.data_root, scripts_dir)
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

    # Vamos acumular os caminhos finais (após renomear) para cópia posterior
    final_docx_paths: list[Path] = []

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

        final_docx_paths.append(new_docx)
        print("✅", new_docx.name)

    print("\n✅ Normalização concluída.")

    # Copiar para DOCX_NORMALIZADOS (se solicitado)
    if args.copiar_normalizados:
        dest_dir = copiar_para_docx_normalizados(base, chosen, final_docx_paths)
        print(f"\n📦 Cópia (sem mover) para: {dest_dir}")

    # “Pergunta de continuidade” (sem executar outros scripts; só sugere)
    if args.modo != "nenhum":
        print("\n➡️ Próximo passo sugerido:")
        if args.modo == "publicacao":
            print("   - Continue o pipeline de PUBLICAÇÃO (consolidação/importação).")
        elif args.modo == "sermoes":
            print("   - Use a pasta DOCX_NORMALIZADOS para listagem de páginas e seleção do artigo-teste.")
        print("   (Observação: este script não executa o próximo passo automaticamente.)")


if __name__ == "__main__":
    main()