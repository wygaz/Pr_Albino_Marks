import os
import re
import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pralbinomarks.settings")

import django
django.setup()

from django.core.files import File
from django.utils.text import slugify
from sermoes.models import Sermao


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extrair_body_html(html_path: Path) -> str:
    html = read_text(html_path)
    m = re.search(r"<body[^>]*>(.*?)</body>", html, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return html.strip()


def replace_file(field, src_path: Path, target_name: str):
    if not src_path or not src_path.exists():
        return

    # Remove arquivo anterior, se existir
    if getattr(field, "name", None):
        field.delete(save=False)

    with src_path.open("rb") as f:
        field.save(target_name, File(f), save=False)


def main():
    parser = argparse.ArgumentParser(
        description="Publica ou atualiza um sermão no app Django 'sermoes'."
    )

    parser.add_argument("--titulo", required=True)
    parser.add_argument("--serie", default="")
    parser.add_argument("--resumo", default="")
    parser.add_argument("--slug", default="")
    parser.add_argument("--ordem", type=int, default=0)
    parser.add_argument("--visivel", action="store_true")

    parser.add_argument("--html-conteudo", default="")
    parser.add_argument("--html-a4", default="")
    parser.add_argument("--pdf-tablet", default="")
    parser.add_argument("--pdf-a4", default="")
    parser.add_argument("--pdf-a5", default="")
    parser.add_argument("--docx-a4", default="")

    args = parser.parse_args()

    titulo = args.titulo.strip()
    slug = args.slug.strip() or slugify(titulo)

    html_conteudo = Path(args.html_conteudo) if args.html_conteudo else None
    html_a4 = Path(args.html_a4) if args.html_a4 else None

    pdf_tablet = Path(args.pdf_tablet) if args.pdf_tablet else None
    pdf_a4 = Path(args.pdf_a4) if args.pdf_a4 else None
    pdf_a5 = Path(args.pdf_a5) if args.pdf_a5 else None
    docx_a4 = Path(args.docx_a4) if args.docx_a4 else None

    # Se não vier html-conteudo, usa o html A4 como fonte do conteúdo do site
    fonte_html = html_conteudo or html_a4

    if not fonte_html or not fonte_html.exists():
        raise FileNotFoundError(
            "Você precisa informar --html-conteudo ou --html-a4 com um arquivo existente."
        )

    conteudo_html = extrair_body_html(fonte_html)

    obj, created = Sermao.objects.get_or_create(
        slug=slug,
        defaults={
            "titulo": titulo,
        }
    )

    obj.titulo = titulo
    obj.slug = slug
    obj.serie = args.serie.strip()
    obj.resumo = args.resumo.strip()
    obj.conteudo_html = conteudo_html
    obj.ordem = args.ordem
    obj.visivel = args.visivel

    # Anexos
    replace_file(obj.pdf_tablet, pdf_tablet, f"{slug}.pdf")
    replace_file(obj.pdf_a4, pdf_a4, f"{slug}.pdf")
    replace_file(obj.pdf_a5, pdf_a5, f"{slug}.pdf")
    replace_file(obj.docx_a4, docx_a4, f"{slug}.docx")

    obj.save()

    print()
    print("[OK] Sermão publicado/atualizado com sucesso.")
    print(f"      Título : {obj.titulo}")
    print(f"      Slug   : {obj.slug}")
    print(f"      URL    : /sermoes/{obj.slug}/")
    print(f"      Criado?: {'sim' if created else 'não (atualizado)'}")
    print()


if __name__ == "__main__":
    main()