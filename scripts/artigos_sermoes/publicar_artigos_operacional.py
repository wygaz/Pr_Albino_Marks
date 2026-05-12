from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

from django.core.files import File
from django.core.files.storage import default_storage
from django.utils import timezone

from artigos_operacional_utils import article_entries, ascii_slug, clean_article_title, repo_root_from_here, safe_filename, serie_nome_from_dirname


def setup_django(root: Path, settings_module: str | None) -> None:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module or "pralbinomarks.settings")
    import django

    django.setup()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publica artigos da base operacional no Django.")
    parser.add_argument("--series-root", default="", help="Default: Apenas_Local/operacional/artigos/series")
    parser.add_argument("--pdf-root", default="", help="Default: Apenas_Local/operacional/artigos/pdfs")
    parser.add_argument("--img-root", default="", help="Default: Apenas_Local/operacional/artigos/imagens")
    parser.add_argument("--docx-path", default="", help="Publica apenas o DOCX informado.")
    parser.add_argument("--django-settings", default="pralbinomarks.settings")
    parser.add_argument("--autor", default="Pr. Albino Marks")
    parser.add_argument("--publish-kinds", default="all", help="all | docx | pdf | img | docx,pdf | docx,img | pdf,img")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--overwrite-media", action="store_true")
    return parser


def should_write(field, overwrite: bool) -> bool:
    if overwrite:
        return True
    if not field:
        return True
    try:
        return not field.storage.exists(field.name)
    except Exception:
        return False


def parse_publish_kinds(raw: str) -> set[str]:
    kinds = {part.strip().lower() for part in str(raw or "").split(",") if part.strip()}
    if not kinds or "all" in kinds:
        return {"docx", "pdf", "img"}
    return {kind for kind in kinds if kind in {"docx", "pdf", "img"}}


def resolve_image_path(img_root: Path, entry) -> Path | None:
    if not img_root.exists():
        return None
    serie_img_dir = img_root / entry.serie_dir.name
    if not serie_img_dir.exists():
        return None

    candidates = []
    base_title = safe_filename(clean_article_title(entry.titulo))
    slug_title = ascii_slug(clean_article_title(entry.titulo))
    candidates.extend(
        [
            entry.docx_path.stem,
            re.sub(r"^\d{1,3}__+", "", entry.docx_path.stem),
            re.sub(r"^\d{1,3}_+", "", entry.docx_path.stem),
            base_title,
            slug_title,
        ]
    )
    seen = set()
    ordered = []
    for item in candidates:
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    for stem in ordered:
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            cand = serie_img_dir / f"{stem}{ext}"
            if cand.exists():
                return cand
    return None


def current_publish_target() -> str:
    env_name = os.getenv("ENV_NAME", "local").strip().lower()
    return "remote" if env_name not in {"", "local"} else "local"


def prepare_remote_storage_for_canonical_save(artigo) -> None:
    try:
        setattr(default_storage, "file_overwrite", True)
    except Exception:
        pass
    for field_name in ("arquivo_word", "arquivo_pdf", "imagem_capa"):
        try:
            storage = getattr(getattr(artigo, field_name), "storage", None)
            if storage is not None:
                setattr(storage, "file_overwrite", True)
        except Exception:
            pass


def publication_status_path(root: Path) -> Path:
    return root / "Apenas_Local" / "scripts" / "homologacao" / "publicacao_artigos_status.json"


def load_publication_status(root: Path) -> dict:
    path = publication_status_path(root)
    if not path.exists():
        return {"items": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"items": {}}
    if not isinstance(data, dict):
        return {"items": {}}
    items = data.get("items")
    if not isinstance(items, dict):
        data["items"] = {}
    return data


def save_publication_status(root: Path, data: dict) -> None:
    path = publication_status_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data["_meta"] = {"updated_at": datetime.now(dt_timezone.utc).isoformat()}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def update_publication_status(root: Path, slug: str, titulo: str, target: str, kinds: set[str]) -> None:
    data = load_publication_status(root)
    items = data.setdefault("items", {})
    entry = items.setdefault(slug, {"slug": slug, "titulo": titulo, "targets": {}})
    entry["titulo"] = titulo
    targets = entry.setdefault("targets", {})
    target_entry = targets.setdefault(target, {})
    for kind in ["docx", "pdf", "img"]:
        if kind in kinds:
            target_entry[kind] = True
    target_entry["updated_at"] = datetime.now(dt_timezone.utc).isoformat()
    save_publication_status(root, data)


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root_from_here()
    setup_django(root, args.django_settings)

    from A_Lei_no_NT.models import Area, Artigo, Autor
    from A_Lei_no_NT.utils import docx_para_html, gerar_slug

    series_root = Path(args.series_root).resolve() if args.series_root else root / "Apenas_Local" / "operacional" / "artigos" / "series"
    pdf_root = Path(args.pdf_root).resolve() if args.pdf_root else root / "Apenas_Local" / "operacional" / "artigos" / "pdfs"
    img_root = Path(args.img_root).resolve() if args.img_root else root / "Apenas_Local" / "operacional" / "artigos" / "imagens"

    entries = article_entries(series_root)
    if args.docx_path:
        docx_target = Path(args.docx_path).resolve()
        entries = [entry for entry in entries if entry.docx_path.resolve() == docx_target]
    if args.limit and args.limit > 0:
        entries = entries[: args.limit]

    autor_obj, _ = Autor.objects.get_or_create(nome=args.autor)
    ok = 0
    fail = 0
    total = len(entries)
    publish_kinds = parse_publish_kinds(args.publish_kinds)
    publish_target = current_publish_target()

    for idx, entry in enumerate(entries, start=1):
        pct = int((idx / total) * 100) if total else 100
        print(f"[{idx}/{total} | {pct:3d}%] Publicar artigo: {entry.titulo}")
        try:
            area_nome = serie_nome_from_dirname(entry.serie_dir.name)
            area_obj, _ = Area.objects.get_or_create(nome=area_nome, defaults={"visivel": True})

            artigo = Artigo.objects.filter(titulo=entry.titulo, area=area_obj).first()
            if artigo is None:
                artigo = Artigo(titulo=entry.titulo, area=area_obj)

            artigo.autor = autor_obj
            artigo.area = area_obj
            artigo.ordem = entry.ordem or artigo.ordem
            artigo.visivel = True
            if not artigo.publicado_em:
                artigo.publicado_em = timezone.now()

            if not artigo.slug:
                artigo.slug = gerar_slug(clean_article_title(entry.titulo))

            if publish_target == "remote":
                prepare_remote_storage_for_canonical_save(artigo)

            print("  [1/3] Convertendo DOCX para HTML...")
            html, *_ = docx_para_html(str(entry.docx_path))
            if html:
                artigo.conteudo_html = html

            pdf_path = pdf_root / entry.serie_dir.name / f"{entry.docx_path.stem}.pdf"
            image_path = resolve_image_path(img_root, entry)

            if args.dry_run:
                print(f"  [DRY] {entry.serie_dir.name} | {entry.ordem:02d} | {entry.titulo} | slug={artigo.slug} | tipos={','.join(sorted(publish_kinds))}")
                ok += 1
                continue

            print("  [2/3] Atualizando registro e anexos...")
            artigo.save()
            slug_final = artigo.slug

            if "docx" in publish_kinds and entry.docx_path.exists() and should_write(artigo.arquivo_word, args.overwrite_media):
                with open(entry.docx_path, "rb") as handle:
                    artigo.arquivo_word.save(f"{slug_final}.docx", File(handle), save=False)
                print("    [OK] DOCX")
            elif "docx" in publish_kinds:
                print("    [SKIP] DOCX")

            if "pdf" in publish_kinds and pdf_path.exists() and should_write(artigo.arquivo_pdf, args.overwrite_media):
                with open(pdf_path, "rb") as handle:
                    artigo.arquivo_pdf.save(f"{slug_final}.pdf", File(handle), save=False)
                print("    [OK] PDF")
            elif "pdf" in publish_kinds:
                print("    [SKIP] PDF")

            if "img" in publish_kinds and image_path and should_write(artigo.imagem_capa, args.overwrite_media):
                ext = image_path.suffix.lower()
                with open(image_path, "rb") as handle:
                    artigo.imagem_capa.save(f"{slug_final}{ext}", File(handle), save=False)
                print("    [OK] IMG")
            elif "img" in publish_kinds:
                print("    [SKIP] IMG")

            print("  [3/3] Salvando artigo...")
            artigo.save()
            ok += 1
            update_publication_status(root, slug_final, entry.titulo, publish_target, publish_kinds)
            print(f"  [OK] {entry.titulo} -> {slug_final} | tipos={','.join(sorted(publish_kinds))}")
        except Exception as exc:  # noqa: BLE001
            fail += 1
            print(f"  [ERRO] {entry.titulo}: {exc}")

    print(f"[OK] Artigos processados: {ok}")
    print(f"[OK] Artigos com erro : {fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
