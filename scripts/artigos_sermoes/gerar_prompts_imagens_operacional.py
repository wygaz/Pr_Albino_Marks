from __future__ import annotations

import argparse
import csv
from pathlib import Path

from artigos_operacional_utils import article_entries, ascii_slug, repo_root_from_here, summary_from_docx


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gera prompts de imagem para os artigos da base operacional.")
    parser.add_argument("--series-root", default="", help="Default: Apenas_Local/operacional/artigos/series")
    parser.add_argument("--out-root", default="", help="Default: Apenas_Local/operacional/artigos/prompts_imagem")
    parser.add_argument("--docx-path", default="", help="Gera apenas para o DOCX informado.")
    parser.add_argument("--npar", type=int, default=5)
    parser.add_argument("--maxchars", type=int, default=420)
    parser.add_argument("--limit", type=int, default=0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root_from_here()
    series_root = Path(args.series_root).resolve() if args.series_root else root / "Apenas_Local" / "operacional" / "artigos" / "series"
    out_root = Path(args.out_root).resolve() if args.out_root else root / "Apenas_Local" / "operacional" / "artigos" / "prompts_imagem"
    out_root.mkdir(parents=True, exist_ok=True)

    entries = article_entries(series_root)
    if args.docx_path:
        docx_target = Path(args.docx_path).resolve()
        entries = [entry for entry in entries if entry.docx_path.resolve() == docx_target]
    if args.limit and args.limit > 0:
        entries = entries[: args.limit]

    rows: list[dict] = []
    for entry in entries:
        resumo = summary_from_docx(entry.docx_path, n_par=args.npar, max_chars=args.maxchars)
        prompt = (
            "Ilustracao de capa, sem texto, sem letras, sem numeros. "
            f"Serie: {entry.serie_nome}. "
            f"Artigo: {entry.titulo}. "
            f"Contexto: {resumo}. "
            "Estilo: pintura digital semi-realista, cinematografica, reverente, biblica, historica, alta qualidade."
        )
        serie_dir = out_root / entry.serie_dir.name
        serie_dir.mkdir(parents=True, exist_ok=True)
        rows.append(
            {
                "serie_dir": entry.serie_dir.name,
                "serie_nome": entry.serie_nome,
                "ordem": entry.ordem,
                "titulo": entry.titulo,
                "docx_path": str(entry.docx_path),
                "arquivo_sugerido": f"{ascii_slug(entry.titulo)}.png",
                "prompt": prompt,
            }
        )

    csv_path = out_root / "prompts_imagens_operacional.csv"
    txt_path = out_root / "prompts_imagens_operacional.txt"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["serie_dir", "serie_nome", "ordem", "titulo", "docx_path", "arquivo_sugerido", "prompt"],
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(rows)

    with txt_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(f"### {row['serie_dir']} | {row['arquivo_sugerido']}\n")
            handle.write(row["prompt"] + "\n\n---\n\n")

    print(f"[OK] Prompts gerados : {len(rows)}")
    print(f"[OK] CSV             : {csv_path}")
    print(f"[OK] TXT             : {txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
