import os
import re
import sys
import argparse
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


BASE_DIR = repo_root_from_here()
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pralbinomarks.settings")

import django
django.setup()

from django.core.files import File
from django.utils.text import slugify
from A_Lei_no_NT.models import Artigo
from sermoes.models import Sermao
from artigos_operacional_utils import strip_editorial_prefixes

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[ERRO] Playwright não está instalado no venv.")
    print("Instale com:")
    print("  pip install playwright")
    print("  playwright install")
    raise


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_body_html(html_path: Path) -> str:
    html = read_text(html_path)
    m = re.search(r"<body[^>]*>(.*?)</body>", html, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return html.strip()


def ensure_exists(path_str: str | None, label: str, required: bool = False) -> Path | None:
    if not path_str:
        if required:
            raise FileNotFoundError(f"[ERRO] Caminho obrigatório ausente: {label}")
        return None
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"[ERRO] Arquivo não encontrado em {label}: {path}")
    return path


def replace_file(field, src_path: Path | None, target_name: str):
    if not src_path:
        return
    if getattr(field, "name", None):
        field.delete(save=False)
    with src_path.open("rb") as f:
        field.save(target_name, File(f), save=False)


def html_to_pdf(html_path: Path, pdf_path: Path, mode: str = "print", width: str | None = None, height: str | None = None):
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    url = html_path.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="load")
        page.emulate_media(media="screen" if mode == "screen" else "print")
        pdf_kwargs = {
            "path": str(pdf_path),
            "print_background": True,
            "prefer_css_page_size": True,
            "margin": {"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
        }
        if width and height:
            pdf_kwargs["width"] = width
            pdf_kwargs["height"] = height
        page.pdf(**pdf_kwargs)
        browser.close()


def build_pdf_name_from_html(html_path: Path, outdir: Path | None = None) -> Path:
    pdf_name = html_path.with_suffix(".pdf").name
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)
        return outdir / pdf_name
    return html_path.with_suffix(".pdf")


def normalize_serie_value(raw: str | None, artigo_canonico) -> str:
    if artigo_canonico is not None:
        area = getattr(artigo_canonico, "area", None)
        area_nome = (getattr(area, "nome", "") or "").strip()
        if area_nome:
            return area_nome
    return (raw or "").strip()


def main():
    parser = argparse.ArgumentParser(description="Converte HTML(s) em PDF(s) e publica/atualiza um sermão no app Django 'sermoes'.")
    parser.add_argument("--titulo", required=True)
    parser.add_argument("--serie", default="")
    parser.add_argument("--resumo", default="")
    parser.add_argument("--slug", default="")
    parser.add_argument("--ordem", type=int, default=0)
    parser.add_argument("--visivel", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--html-a4", required=True)
    parser.add_argument("--html-a5", default="")
    parser.add_argument("--html-tablet", default="")
    parser.add_argument("--docx-a4", default="")
    parser.add_argument("--relatorio-html", default="")
    parser.add_argument("--pdf-outdir", default="")
    parser.add_argument("--tablet-width", default="160mm")
    parser.add_argument("--tablet-height", default="240mm")
    args = parser.parse_args()

    titulo = strip_editorial_prefixes(args.titulo).strip()
    slug = args.slug.strip() or slugify(titulo)
    html_a4 = ensure_exists(args.html_a4, "--html-a4", required=True)
    html_a5 = ensure_exists(args.html_a5, "--html-a5")
    html_tablet = ensure_exists(args.html_tablet, "--html-tablet")
    docx_a4 = ensure_exists(args.docx_a4, "--docx-a4")
    relatorio_html = ensure_exists(args.relatorio_html, "--relatorio-html")
    pdf_outdir = Path(args.pdf_outdir) if args.pdf_outdir else None

    print("[1/4] Convertendo HTML para PDF...")
    pdf_a4 = build_pdf_name_from_html(html_a4, pdf_outdir)
    html_to_pdf(html_a4, pdf_a4, mode="print")
    print(f"  [OK] A4 -> {pdf_a4}")

    pdf_a5 = None
    if html_a5:
        pdf_a5 = build_pdf_name_from_html(html_a5, pdf_outdir)
        html_to_pdf(html_a5, pdf_a5, mode="print")
        print(f"  [OK] A5 -> {pdf_a5}")

    pdf_tablet = None
    if html_tablet:
        pdf_tablet = build_pdf_name_from_html(html_tablet, pdf_outdir)
        html_to_pdf(html_tablet, pdf_tablet, mode="screen", width=args.tablet_width, height=args.tablet_height)
        print(f"  [OK] Tablet -> {pdf_tablet}")

    relatorio_pdf = None
    if relatorio_html:
        relatorio_pdf = build_pdf_name_from_html(relatorio_html, pdf_outdir)
        html_to_pdf(relatorio_html, relatorio_pdf, mode="print")
        print(f"  [OK] Relatorio -> {relatorio_pdf}")

    print("[2/4] Extraindo conteúdo HTML para o site...")
    conteudo_html = extract_body_html(html_a4)

    print("[3/4] Criando/atualizando registro no Django...")
    artigo_canonico = None
    if slug:
        artigo_canonico = Artigo.objects.filter(slug=slug, visivel=True).first()
    if artigo_canonico is None and titulo:
        artigo_canonico = Artigo.objects.filter(titulo__iexact=titulo, visivel=True).first()
    titulo_canonico = (getattr(artigo_canonico, "titulo", "") or "").strip() or titulo
    resumo = (args.resumo or "").strip()
    if resumo.lower().startswith("sermão publicado em lote:".lower()) or resumo.lower().startswith("sermao publicado em lote:"):
        resumo = titulo_canonico

    serie_final = normalize_serie_value(args.serie, artigo_canonico)

    obj, created = Sermao.objects.get_or_create(slug=slug, defaults={"titulo": titulo})
    obj.titulo = titulo_canonico
    obj.slug = slug
    obj.serie = serie_final
    obj.resumo = resumo
    obj.conteudo_html = conteudo_html
    obj.ordem = args.ordem
    obj.visivel = args.visivel
    print("  [3.1/4] Atualizando anexos...")
    replace_file(obj.pdf_a4, pdf_a4, pdf_a4.name)
    replace_file(obj.pdf_a5, pdf_a5, pdf_a5.name if pdf_a5 else f"{slug}__A5.pdf")
    replace_file(obj.pdf_tablet, pdf_tablet, pdf_tablet.name if pdf_tablet else f"{slug}__tablet.pdf")
    replace_file(obj.relatorio_tecnico_pdf, relatorio_pdf, relatorio_pdf.name if relatorio_pdf else f"{slug}__relatorio-tecnico.pdf")
    replace_file(obj.docx_a4, docx_a4, docx_a4.name if docx_a4 else f"{slug}.docx")
    print("  [3.2/4] Salvando sermao...")
    obj.save()

    print("[4/4] Concluído.")
    print()
    print("[OK] Sermão publicado/atualizado com sucesso.")
    print(f"     Título : {obj.titulo}")
    print(f"     Slug   : {obj.slug}")
    print(f"     URL    : /sermoes/{obj.slug}/")
    print(f"     Criado?: {'sim' if created else 'não (atualizado)'}")


if __name__ == "__main__":
    main()

