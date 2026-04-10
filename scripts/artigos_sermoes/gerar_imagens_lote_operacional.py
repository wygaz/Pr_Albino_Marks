from __future__ import annotations

import argparse
import base64
import csv
import os
import time
from pathlib import Path

from openai import OpenAI
from artigos_operacional_utils import SERIE_DISPLAY_BY_ID, ascii_slug


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gera imagens dos artigos na base operacional a partir do CSV de prompts.")
    parser.add_argument("--prompts-csv", default="", help="Default: prefere Apenas_Local/operacional/artigos/prompts_imagem/pr_albino_prompts_ricos_58_artigos.csv e cai para prompts_imagens_operacional.csv")
    parser.add_argument("--out-root", default="", help="Default: Apenas_Local/operacional/artigos/imagens")
    parser.add_argument("--docx-path", default="", help="Gera apenas para o DOCX informado.")
    parser.add_argument("--model", default="gpt-image-1")
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default="low", choices=["low", "medium", "high", "auto"])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--run", action="store_true", help="Sem --run, apenas simula.")
    parser.add_argument("--sleep", type=float, default=1.2)
    return parser


def serie_dir_from_row(row: dict) -> str:
    explicit = str(row.get("serie_dir", "") or "").strip()
    if explicit:
        return explicit
    serie_raw = str(row.get("serie", "") or "").strip()
    if serie_raw.isdigit():
        serie_id = int(serie_raw)
        serie_nome = SERIE_DISPLAY_BY_ID.get(serie_id, f"serie-{serie_id}")
        return f"Serie_{serie_id}__{ascii_slug(serie_nome)}"
    if serie_raw:
        return ascii_slug(serie_raw)
    return "sem-serie"


def output_name_from_row(row: dict) -> str:
    explicit = str(row.get("arquivo_sugerido", "") or "").strip()
    if explicit:
        return explicit
    slug = str(row.get("slug", "") or "").strip()
    if slug:
        return f"{slug}.png"
    titulo = str(row.get("titulo", "") or "").strip()
    return f"{ascii_slug(titulo)}.png"


def prompt_from_row(row: dict) -> str:
    return str(row.get("prompt", "") or row.get("prompt_rico", "") or "").strip()


def normalized_rows(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        out.append(
            {
                **row,
                "serie_dir": serie_dir_from_row(row),
                "arquivo_sugerido": output_name_from_row(row),
                "prompt_final": prompt_from_row(row),
            }
        )
    return out


def main() -> int:
    args = build_parser().parse_args()
    root = Path(__file__).resolve().parents[3]
    if args.prompts_csv:
        prompts_csv = Path(args.prompts_csv).resolve()
    else:
        prompts_root = root / "Apenas_Local" / "operacional" / "artigos" / "prompts_imagem"
        preferred = prompts_root / "pr_albino_prompts_ricos_58_artigos.csv"
        fallback = prompts_root / "prompts_imagens_operacional.csv"
        prompts_csv = preferred if preferred.exists() else fallback
    out_root = Path(args.out_root).resolve() if args.out_root else root / "Apenas_Local" / "operacional" / "artigos" / "imagens"
    out_root.mkdir(parents=True, exist_ok=True)

    with prompts_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        rows = list(csv.DictReader(handle, delimiter=delimiter))
    rows = normalized_rows(rows)
    if args.docx_path:
        docx_target = str(Path(args.docx_path).resolve())
        rows = [row for row in rows if str(Path(row.get("docx_path", "")).resolve()) == docx_target]
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    if not args.run:
        print(f"[OK] Simulacao. Prompts: {len(rows)}")
        for row in rows:
            out_dir = out_root / row["serie_dir"]
            out_path = out_dir / row["arquivo_sugerido"]
            if out_path.exists() and not args.overwrite:
                print(f"[SKIP_IMAGE_EXISTS] {out_path}")
            else:
                print(f"[SIMULAR] {out_path}")
        return 0

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY nao definida.")
    client = OpenAI(api_key=api_key)

    ok = 0
    fail = 0
    skip = 0
    total = len(rows)
    for idx, row in enumerate(rows, start=1):
        out_dir = out_root / row["serie_dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / row["arquivo_sugerido"]
        pct = int((idx / total) * 100) if total else 100
        print(f"[{idx}/{total} | {pct:3d}%] Imagem artigo: {out_path.name}")
        if out_path.exists() and not args.overwrite:
            skip += 1
            print(f"  [SKIP_IMAGE_EXISTS] {out_path}")
            continue
        try:
            img = client.images.generate(
                model=args.model,
                prompt=row["prompt_final"],
                size=args.size,
                quality=args.quality,
                output_format="png",
            )
            out_path.write_bytes(base64.b64decode(img.data[0].b64_json))
            ok += 1
            print(f"  [OK] {out_path}")
        except Exception as exc:  # noqa: BLE001
            fail += 1
            print(f"  [ERRO] {out_path.name}: {exc}")
        time.sleep(args.sleep)

    print(f"[OK] Imagens geradas : {ok}")
    print(f"[OK] Imagens puladas : {skip}")
    print(f"[OK] Imagens com erro: {fail}")
    print(f"[OK] Pasta de saida  : {out_root}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
