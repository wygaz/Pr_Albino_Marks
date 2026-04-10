import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import csv
import re

try:
    from pypdf import PdfReader
except ImportError:
    raise SystemExit("Instale: pip install pypdf")

def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")[:120] or "arquivo"

def convert_docx_to_pdf(soffice_path: Path, docx: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    # LibreOffice: converte mantendo nome-base
    cmd = [
        str(soffice_path),
        "--headless",
        "--nologo",
        "--nolockcheck",
        "--nodefault",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(docx),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    pdf = out_dir / (docx.stem + ".pdf")
    if not pdf.exists():
        # fallback: busca o PDF gerado
        candidates = list(out_dir.glob("*.pdf"))
        if candidates:
            return candidates[-1]
        raise FileNotFoundError(f"PDF não encontrado para {docx.name}")
    return pdf

def pdf_page_count(pdf: Path) -> int:
    r = PdfReader(str(pdf))
    return len(r.pages)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True, help="Pasta com DOCX normalizados")
    ap.add_argument("--saida", required=True, help="Pasta onde salvar relatório (CSV)")
    ap.add_argument("--soffice", default="", help="Caminho para soffice.exe (LibreOffice). Se vazio, tenta achar no PATH.")
    ap.add_argument("--max", type=int, default=0, help="Limite de arquivos para teste (0 = todos)")
    ap.add_argument("--keep-pdfs", action="store_true", help="Mantém PDFs convertidos (senão apaga ao final)")
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    out_root = Path(args.saida)
    out_root.mkdir(parents=True, exist_ok=True)

    soffice = Path(args.soffice) if args.soffice else Path("soffice")
    tmp_pdf_dir = out_root / "_tmp_pdfs"

    docxs = sorted(input_dir.glob("*.docx"))
    if args.max and args.max > 0:
        docxs = docxs[:args.max]

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = out_root / f"relatorio_docx_paginas_{stamp}.csv"

    rows = []
    print(f"[INFO] DOCX encontrados: {len(docxs)}")
    for i, docx in enumerate(docxs, start=1):
        try:
            pdf = convert_docx_to_pdf(soffice, docx, tmp_pdf_dir)
            pages = pdf_page_count(pdf)
            rows.append({
                "ordem": i,
                "arquivo_docx": docx.name,
                "titulo_base": docx.stem,
                "paginas_pdf": pages,
                "tamanho_kb": round(docx.stat().st_size / 1024, 1),
                "caminho_docx": str(docx),
            })
            print(f"[OK] ({i}/{len(docxs)}) {docx.name} -> {pages} pág.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] LibreOffice falhou em {docx.name}: {e}")
        except Exception as e:
            print(f"[ERRO] {docx.name}: {e}")

    # salva CSV (UTF-8-SIG abre bem no Excel)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        if rows:
            w.writeheader()
            w.writerows(rows)

    print(f"[OK] CSV: {csv_path}")

    if not args.keep_pdfs and tmp_pdf_dir.exists():
        for p in tmp_pdf_dir.glob("*"):
            try:
                p.unlink()
            except:
                pass
        try:
            tmp_pdf_dir.rmdir()
        except:
            pass
        print("[OK] PDFs temporários removidos.")

if __name__ == "__main__":
    main()