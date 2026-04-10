from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def repo_root_from_here() -> Path:
    cur = Path(__file__).resolve().parent
    for _ in range(10):
        if (cur / "manage.py").exists() or (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError("Raiz do projeto nao encontrada.")


def setup_django(root: Path, settings_module: str) -> None:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    import django

    django.setup()


def field_name(field) -> str:
    try:
        return str(getattr(field, "name", "") or "").strip()
    except Exception:
        return ""


def delete_field_file(storage, field, *, execute: bool) -> tuple[str, str]:
    name = field_name(field)
    if not name:
        return "", ""
    if not execute:
        return name, "DRY_DELETE_FILE"
    try:
        if storage.exists(name):
            storage.delete(name)
        return name, "FILE_DELETED"
    except Exception as exc:  # noqa: BLE001
        return name, f"FILE_ERROR: {exc}"


def delete_storage_prefixes(storage, prefixes: list[str], *, execute: bool) -> list[dict]:
    rows: list[dict] = []
    for prefix in prefixes:
        try:
            _dirs, files = storage.listdir(prefix)
        except Exception:
            continue
        for rel in files:
            name = f"{prefix.rstrip('/')}/{rel}".replace("\\", "/")
            if not execute:
                rows.append({"kind": "orphan_media", "target": name, "status": "DRY_DELETE_FILE"})
                continue
            try:
                if storage.exists(name):
                    storage.delete(name)
                rows.append({"kind": "orphan_media", "target": name, "status": "FILE_DELETED"})
            except Exception as exc:  # noqa: BLE001
                rows.append({"kind": "orphan_media", "target": name, "status": f"FILE_ERROR: {exc}"})
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reseta a publicacao local do site, preservando cadastro e as imagens-fonte do operacional."
    )
    parser.add_argument("--django-settings", default="pralbinomarks.settings")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--keep-taxonomy",
        action="store_true",
        help="Preserva Area e Autor. Sem esta flag, ambos sao removidos para republicacao integral.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root_from_here()
    setup_django(root, args.django_settings)

    from django.core.files.storage import default_storage
    from A_Lei_no_NT.models import Area, Artigo, Autor
    from sermoes.models import Sermao

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = root / "Apenas_Local" / "scripts" / "homologacao"
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / f"reset_publicacao_local_{stamp}.csv"
    json_path = report_dir / f"reset_publicacao_local_{stamp}.json"

    execute = bool(args.execute)
    rows: list[dict] = []

    artigos = list(Artigo.objects.all().order_by("id"))
    sermoes = list(Sermao.objects.all().order_by("id"))
    areas = list(Area.objects.all().order_by("id"))
    autores = list(Autor.objects.all().order_by("id"))

    for sermao in sermoes:
        for label, field in [
            ("pdf_tablet", sermao.pdf_tablet),
            ("pdf_a4", sermao.pdf_a4),
            ("pdf_a5", sermao.pdf_a5),
            ("relatorio_tecnico_pdf", sermao.relatorio_tecnico_pdf),
            ("docx_a4", sermao.docx_a4),
            ("imagem_capa", sermao.imagem_capa),
        ]:
            target, status = delete_field_file(default_storage, field, execute=execute)
            if target:
                rows.append(
                    {
                        "kind": "sermao_file",
                        "object_id": sermao.id,
                        "title": sermao.titulo,
                        "field": label,
                        "target": target,
                        "status": status,
                    }
                )
        rows.append(
            {
                "kind": "sermao_record",
                "object_id": sermao.id,
                "title": sermao.titulo,
                "field": "",
                "target": sermao.slug,
                "status": "DRY_DELETE_RECORD" if not execute else "RECORD_DELETED",
            }
        )
        if execute:
            sermao.delete()

    for artigo in artigos:
        for label, field in [
            ("arquivo_word", artigo.arquivo_word),
            ("arquivo_pdf", artigo.arquivo_pdf),
            ("imagem_capa", artigo.imagem_capa),
        ]:
            target, status = delete_field_file(default_storage, field, execute=execute)
            if target:
                rows.append(
                    {
                        "kind": "artigo_file",
                        "object_id": artigo.id,
                        "title": artigo.titulo,
                        "field": label,
                        "target": target,
                        "status": status,
                    }
                )
        rows.append(
            {
                "kind": "artigo_record",
                "object_id": artigo.id,
                "title": artigo.titulo,
                "field": "",
                "target": artigo.slug,
                "status": "DRY_DELETE_RECORD" if not execute else "RECORD_DELETED",
            }
        )
        if execute:
            artigo.delete()

    if not args.keep_taxonomy:
        for area in areas:
            rows.append(
                {
                    "kind": "area_record",
                    "object_id": area.id,
                    "title": area.nome,
                    "field": "",
                    "target": area.nome,
                    "status": "DRY_DELETE_RECORD" if not execute else "RECORD_DELETED",
                }
            )
            if execute:
                area.delete()
        for autor in autores:
            rows.append(
                {
                    "kind": "autor_record",
                    "object_id": autor.id,
                    "title": autor.nome,
                    "field": "",
                    "target": autor.nome,
                    "status": "DRY_DELETE_RECORD" if not execute else "RECORD_DELETED",
                }
            )
            if execute:
                autor.delete()

    rows.extend(
        delete_storage_prefixes(
            default_storage,
            prefixes=[
                "pdfs/sermoes/tablet",
                "pdfs/sermoes/a4",
                "pdfs/sermoes/a5",
                "pdfs/relatorios_tecnicos",
                "docs/sermoes",
                "imagens/sermoes",
                "pdfs/artigos",
                "uploads/artigos",
                "imagens/artigos",
            ],
            execute=execute,
        )
    )

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["kind", "object_id", "title", "field", "target", "status"])
        writer.writeheader()
        writer.writerows(rows)

    post_counts = {
        "artigos": Artigo.objects.count(),
        "sermoes": Sermao.objects.count(),
        "areas": Area.objects.count(),
        "autores": Autor.objects.count(),
    }
    verification = {
        "artigos_ok": (post_counts["artigos"] == 0) if execute else True,
        "sermoes_ok": (post_counts["sermoes"] == 0) if execute else True,
        "areas_ok": (post_counts["areas"] == len(areas)) if (execute and args.keep_taxonomy) else ((post_counts["areas"] == 0) if execute else True),
        "autores_ok": (post_counts["autores"] == len(autores)) if (execute and args.keep_taxonomy) else ((post_counts["autores"] == 0) if execute else True),
    }
    verification["reset_ok"] = all(verification.values())

    payload = {
        "mode": "EXECUTE" if execute else "DRY-RUN",
        "keep_taxonomy": bool(args.keep_taxonomy),
        "counts": {
            "artigos": len(artigos),
            "sermoes": len(sermoes),
            "areas": len(areas),
            "autores": len(autores),
            "rows": len(rows),
        },
        "post_counts": post_counts,
        "verification": verification,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] Modo          : {'EXECUTE' if execute else 'DRY-RUN'}")
    print(f"[OK] Artigos       : {len(artigos)}")
    print(f"[OK] Sermoes       : {len(sermoes)}")
    print(f"[OK] Areas         : {len(areas)}")
    print(f"[OK] Autores       : {len(autores)}")
    print(f"[OK] Restantes     : artigos={post_counts['artigos']} | sermoes={post_counts['sermoes']} | areas={post_counts['areas']} | autores={post_counts['autores']}")
    print(f"[OK] Verificacao   : {'RESET_CONFIRMADO' if verification['reset_ok'] else 'RESET_INCONSISTENTE'}")
    print(f"[OK] Relatorio CSV : {csv_path}")
    print(f"[OK] Relatorio JSON: {json_path}")
    return 0 if (not execute or verification["reset_ok"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
