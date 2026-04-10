from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path


def repo_root_from_here() -> Path:
    cur = Path(__file__).resolve().parent
    for _ in range(8):
        if (cur / "manage.py").exists() or (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError("Raiz do projeto nao encontrada.")


def ensure_operational_tree(base: Path) -> dict[str, Path]:
    paths = {
        "root": base,
        "relatorios": base / "relatorios",
        "artigos_series": base / "artigos" / "series",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def clear_dir_contents(path: Path) -> None:
    if not path.exists():
        return
    for item in path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def copy_tree(src: Path, dst: Path) -> int:
    copied = 0
    for file_path in src.rglob("*"):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(src)
        dst_file = dst / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dst_file)
        copied += 1
    return copied


def promote_series(lote_dir: Path, operational_root: Path, clear_existing: bool) -> dict:
    ambiente = lote_dir / "ambiente_operacional"
    if not ambiente.exists():
        raise FileNotFoundError(f"Ambiente operacional do lote nao encontrado: {ambiente}")

    serie_dirs = sorted([p for p in ambiente.glob("Serie_*") if p.is_dir()])
    if not serie_dirs:
        raise RuntimeError(f"Nenhuma pasta Serie_* encontrada em {ambiente}")

    paths = ensure_operational_tree(operational_root)
    series_target = paths["artigos_series"]
    if clear_existing:
        clear_dir_contents(series_target)

    report_rows: list[dict] = []
    total_files = 0
    for serie_dir in serie_dirs:
        dst = series_target / serie_dir.name
        copied = copy_tree(serie_dir, dst)
        total_files += copied
        report_rows.append(
            {
                "serie_dir": serie_dir.name,
                "origem": str(serie_dir),
                "destino": str(dst),
                "arquivos_copiados": copied,
            }
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = paths["relatorios"]
    csv_path = report_dir / f"promocao_lote_{lote_dir.name}_{stamp}.csv"
    json_path = report_dir / f"promocao_lote_{lote_dir.name}_{stamp}.json"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["serie_dir", "origem", "destino", "arquivos_copiados"])
        writer.writeheader()
        writer.writerows(report_rows)

    json_path.write_text(
        json.dumps(
            {
                "lote": lote_dir.name,
                "lote_dir": str(lote_dir),
                "operational_root": str(operational_root),
                "series_target": str(series_target),
                "series_count": len(report_rows),
                "files_count": total_files,
                "rows": report_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "series_count": len(report_rows),
        "files_count": total_files,
        "series_target": str(series_target),
        "csv_path": str(csv_path),
        "json_path": str(json_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Promove as series consolidadas de um lote para a base operacional cumulativa.")
    parser.add_argument("--lote", required=True, help="Nome do lote em Apenas_Local/anexos_filtrados")
    parser.add_argument("--operacional-root", default="", help="Default: Apenas_Local/operacional")
    parser.add_argument("--clear-existing", action="store_true", help="Limpa artigos/series antes da promocao")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root_from_here()
    lote_dir = root / "Apenas_Local" / "anexos_filtrados" / args.lote
    operational_root = Path(args.operacional_root).resolve() if args.operacional_root else root / "Apenas_Local" / "operacional"

    result = promote_series(lote_dir, operational_root, args.clear_existing)
    print(f"[OK] Series promovidas : {result['series_count']}")
    print(f"[OK] Arquivos copiados : {result['files_count']}")
    print(f"[OK] Base operacional  : {result['series_target']}")
    print(f"[OK] Relatorio CSV     : {result['csv_path']}")
    print(f"[OK] Relatorio JSON    : {result['json_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
