from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from artigos_operacional_utils import article_entries, find_soffice, repo_root_from_here


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gera PDFs dos artigos da base operacional usando LibreOffice.")
    parser.add_argument("--series-root", default="", help="Default: Apenas_Local/operacional/artigos/series")
    parser.add_argument("--out-root", default="", help="Default: Apenas_Local/operacional/artigos/pdfs")
    parser.add_argument("--docx-path", default="", help="Gera apenas para o DOCX informado.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    return parser


def convert_docx_to_pdf(soffice: str, docx_path: Path, out_dir: Path) -> None:
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
        str(docx_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "").strip())


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root_from_here()
    series_root = Path(args.series_root).resolve() if args.series_root else root / "Apenas_Local" / "operacional" / "artigos" / "series"
    out_root = Path(args.out_root).resolve() if args.out_root else root / "Apenas_Local" / "operacional" / "artigos" / "pdfs"
    out_root.mkdir(parents=True, exist_ok=True)

    entries = article_entries(series_root)
    if args.docx_path:
        docx_target = Path(args.docx_path).resolve()
        entries = [entry for entry in entries if entry.docx_path.resolve() == docx_target]
    if args.limit and args.limit > 0:
        entries = entries[: args.limit]

    soffice = find_soffice()
    ok = 0
    skip = 0
    fail = 0
    total = len(entries)

    for idx, entry in enumerate(entries, start=1):
        serie_out = out_root / entry.serie_dir.name
        serie_out.mkdir(parents=True, exist_ok=True)
        pdf_path = serie_out / f"{entry.docx_path.stem}.pdf"
        pct = int((idx / total) * 100) if total else 100
        print(f"[{idx}/{total} | {pct:3d}%] PDF artigo: {entry.docx_path.name}")
        if pdf_path.exists() and not args.overwrite:
            skip += 1
            print(f"  [SKIP] {pdf_path.name}")
            continue
        try:
            convert_docx_to_pdf(soffice, entry.docx_path, serie_out)
            ok += 1
            print(f"  [OK] {pdf_path.name}")
        except Exception as exc:  # noqa: BLE001
            fail += 1
            print(f"  [ERRO] {entry.docx_path.name}: {exc}")

    print(f"[OK] PDFs gerados  : {ok}")
    print(f"[OK] PDFs pulados  : {skip}")
    print(f"[OK] PDFs com erro : {fail}")
    print(f"[OK] Pasta de saida: {out_root}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
