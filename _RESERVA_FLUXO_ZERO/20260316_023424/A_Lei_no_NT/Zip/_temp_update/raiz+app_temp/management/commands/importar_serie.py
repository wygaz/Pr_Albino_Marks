import csv
import os
import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from docx import Document

from A_Lei_no_NT.models import Area, Artigo, Autor
from A_Lei_no_NT.utils import docx_para_html


def normalize_key(s: str) -> str:
    s = s or ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    return s.strip()


def strip_sm_prefix(text: str) -> str:
    # remove prefixos do tipo: "Sm1055 " / "SM 1055A " etc.
    return re.sub(r"^\s*sm\s*\d+\w*\s+", "", text, flags=re.IGNORECASE).strip()


def looks_like_sm_title_line(text: str, titulo: str) -> bool:
    t = " ".join(text.split())
    if not re.match(r"^\s*sm\s*\d+", t, flags=re.IGNORECASE):
        return False
    # se depois de tirar "Sm1055" ficar igual ao título, é duplicação
    return normalize_key(strip_sm_prefix(t)) == normalize_key(titulo)


def looks_like_author_line(text: str, autor_nome: str) -> bool:
    t = " ".join(text.split()).strip()
    if not t:
        return False

    # "Autor: Pr. Albino Marks"
    if re.match(r"^autor\s*:\s*", t, flags=re.IGNORECASE):
        return True

    # "1. Albino Marks" / "1) Albino Marks" / "Albino Marks"
    autor_n = normalize_key(autor_nome)
    t_n = normalize_key(t)

    if t_n == autor_n:
        return True

    if re.match(r"^\d+\s*[\.\)\-:]\s*", t):
        t2 = re.sub(r"^\d+\s*[\.\)\-:]\s*", "", t).strip()
        if normalize_key(t2) == autor_n:
            return True

    return False


def clean_html_leading_noise(html: str, titulo: str, autor_nome: str) -> str:
    """
    Remove, apenas no começo do HTML, elementos redundantes:
      - linha "Sm1055 ... <título>" (quando for repetição do título)
      - linha de autor ("Autor: ..." ou "1. Albino Marks")
      - título repetido (se aparecer como 1º elemento)
    """
    from bs4 import BeautifulSoup
    from bs4.element import Tag

    if not html:
        return html

    soup = BeautifulSoup(html, "html.parser")
    container = soup.body if soup.body else soup

    # pega “blocos” iniciais (p/h1/h2/h3) no nível superior
    def top_blocks():
        blocks = []
        for node in list(container.contents):
            if isinstance(node, Tag) and node.name in ("p", "h1", "h2", "h3"):
                blocks.append(node)
        return blocks

    removed = 0
    for _ in range(10):  # evita loop infinito
        blocks = top_blocks()
        if not blocks:
            break
        first = blocks[0]
        txt = first.get_text(" ", strip=True)

        if not txt:
            first.decompose()
            removed += 1
            continue

        # título duplicado como primeiro bloco
        if normalize_key(txt) == normalize_key(titulo):
            first.decompose()
            removed += 1
            continue

        # "Sm1055 <título>"
        if looks_like_sm_title_line(txt, titulo):
            first.decompose()
            removed += 1
            continue

        # linha do autor
        if autor_nome and looks_like_author_line(txt, autor_nome):
            first.decompose()
            removed += 1
            continue

        # se não bateu em nada, para
        break

    # retorna sem wrappers <html><body> caso existam
    return container.decode_contents() if soup.body else str(soup)


def read_esboco_titles(esboco_docx: Path):
    """
    ESBOÇO.docx padrão:
      1ª linha: "ESBOÇO" (descartar)
      2ª linha: nome da série (guardar e descartar da lista)
      3ª linha em diante: títulos dos artigos (ordem 1..N)
    """
    doc = Document(str(esboco_docx))
    lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]

    # descarta a palavra ESBOÇO
    if lines and normalize_key(lines[0]).startswith("esboc"):
        lines = lines[1:]

    serie_title = lines[0].strip() if lines else None
    article_titles = lines[1:] if len(lines) >= 2 else []

    # remove títulos vazios e normaliza espaços
    article_titles = [" ".join(t.split()).strip() for t in article_titles if t.strip()]
    return serie_title, article_titles


class Command(BaseCommand):
    help = "Importa/atualiza uma série a partir de manifest.csv + arquivos (HTML/DOCX/PDF/IMG), obedecendo o ESBOÇO.docx."

    def add_arguments(self, parser):
        parser.add_argument("--serie", required=True, help="Nome da série (nome da pasta dentro do --base).")
        parser.add_argument("--base", default="Apenas_Local/anexos_filtrados/SERIES", help="Pasta base onde estão as séries.")
        parser.add_argument("--manifest", default="manifest.csv", help="Nome do manifest dentro da pasta da série.")
        parser.add_argument("--dry-run", action="store_true", help="Não grava no banco nem envia arquivos.")
        parser.add_argument("--limit", type=int, default=0, help="Processa no máximo N itens (0 = todos).")

        parser.add_argument("--autor", default=None, help="Autor padrão da série (se omitido, pergunta no início).")
        parser.add_argument("--area", default=None, help="Nome da Area (default: usa --serie).")

        parser.add_argument(
            "--ordem-mode",
            default="esboco",
            choices=["esboco", "manifest", "compact", "offset"],
            help="Como definir Artigo.ordem: esboco (recomendado), manifest, compact (1..N), offset (base+1..N).",
        )
        parser.add_argument(
            "--offset-scope",
            default="area",
            choices=["area", "global"],
            help="Quando ordem-mode=offset: base do offset vem do max(ordem) da area ou global.",
        )
        parser.add_argument("--overwrite-media", action="store_true", help="Reenvia/reescreve mídia mesmo se já existir.")
        parser.add_argument("--no-clean-html", action="store_true", help="Não remove Sm/Autor/Título duplicado do HTML.")

    def handle(self, *args, **opt):
        serie = opt["serie"]
        base = Path(opt["base"]).resolve()
        series_dir = (base / serie).resolve()

        manifest_path = series_dir / opt["manifest"]
        if not manifest_path.exists():
            raise SystemExit(f"Não achei manifest: {manifest_path}")

        # Autor padrão (pergunta no início, como você pediu)
        autor_nome = opt["autor"]
        if autor_nome is None:
            entrada = input("Autor da série [Pr. Albino Marks]: ").strip()
            autor_nome = entrada or "Pr. Albino Marks"

        area_nome = opt["area"] or serie

        # Area e Autor no BD
        area_obj, _ = Area.objects.get_or_create(nome=area_nome, defaults={"visivel": True})
        autor_obj, _ = Autor.objects.get_or_create(nome=autor_nome)

        # Ordem por ESBOÇO.docx (recomendado)
        esboco_docx = None
        for cand in ("ESBOÇO.docx", "ESBOCO.docx", "Esboço.docx", "Esboco.docx"):
            p = series_dir / cand
            if p.exists():
                esboco_docx = p
                break

        esboco_map = {}
        if esboco_docx and opt["ordem_mode"] == "esboco":
            _, titles = read_esboco_titles(esboco_docx)
            for idx, t in enumerate(titles, start=1):
                esboco_map[normalize_key(t)] = idx

        # Lê manifest
        with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            items = list(reader)

        if opt["limit"] and opt["limit"] > 0:
            items = items[: opt["limit"]]

        self.stdout.write(self.style.SUCCESS(f"Importando {len(items)} itens da série '{serie}'..."))
        if esboco_docx and opt["ordem_mode"] == "esboco":
            self.stdout.write(f"✅ Ordem vinda de ESBOÇO: {esboco_docx.name}")
        elif opt["ordem_mode"] != "manifest":
            self.stdout.write(f"ℹ️ Ordem-mode: {opt['ordem_mode']}")

        # base para offset
        base_offset = 0
        if opt["ordem_mode"] == "offset":
            qs = Artigo.objects.all()
            if opt["offset_scope"] == "area":
                qs = qs.filter(area=area_obj)
            base_offset = qs.aggregate(m=models.Max("ordem"))["m"] or 0

        html_dir = series_dir / "HTML"
        docx_dir = series_dir / "DOCX"
        pdf_dir = series_dir / "PDF"
        img_dir = series_dir / "IMG"

        ok = 0
        for pos, row in enumerate(items, start=1):
            titulo = (row.get("titulo") or "").strip()
            if not titulo:
                self.stdout.write(self.style.WARNING(f"[{pos}] ⚠️ Sem título no manifest, pulando."))
                continue

            # pega slug/arquivo do manifest
            slug = (row.get("slug") or "").strip()
            docx_name = (row.get("docx") or "").strip()
            pdf_name = (row.get("pdf") or "").strip()
            img_name = (row.get("imagem") or "").strip()

            # ordem
            ordem = None
            if opt["ordem_mode"] == "esboco" and esboco_map:
                ordem = esboco_map.get(normalize_key(titulo))
            elif opt["ordem_mode"] == "manifest":
                try:
                    ordem = int(row.get("ordem") or 0) or None
                except Exception:
                    ordem = None
            elif opt["ordem_mode"] == "compact":
                ordem = pos
            elif opt["ordem_mode"] == "offset":
                ordem = base_offset + pos

            # encontra artigo (preferência por slug)
            artigo = None
            if slug:
                artigo = Artigo.objects.filter(slug=slug).first()
            if artigo is None:
                artigo = Artigo.objects.filter(titulo__iexact=titulo).first()

            creating = artigo is None
            if creating:
                artigo = Artigo(titulo=titulo)
                if slug:
                    artigo.slug = slug

            # HTML (preferir HTML pronto, senão gera do DOCX)
            html = ""
            html_path = html_dir / f"{titulo}.html"
            if html_path.exists():
                html = html_path.read_text(encoding="utf-8", errors="replace")
            else:
                # tenta DOCX
                docx_path = docx_dir / docx_name if docx_name else (docx_dir / f"{titulo}.docx")
                if docx_path.exists():
                    html = docx_para_html(str(docx_path))
                else:
                    self.stdout.write(self.style.WARNING(f"[{pos}] ⚠️ Sem HTML e sem DOCX: {titulo}"))
                    html = ""

            if html and not opt["no_clean_html"]:
                html = clean_html_leading_noise(html, titulo=titulo, autor_nome=autor_nome)

            # aplica campos principais
            artigo.titulo = titulo
            artigo.area = area_obj
            artigo.autor = autor_obj
            if ordem is not None:
                artigo.ordem = ordem
            if html:
                artigo.conteudo_html = html
            if not artigo.publicado_em:
                artigo.publicado_em = timezone.now()

            # mídia: DOCX / PDF / IMG via FileField (funciona com S3)
            def should_write(field):
                if opt["overwrite_media"]:
                    return True
                if not field:
                    return True
                try:
                    return not field.storage.exists(field.name)
                except Exception:
                    return False

            # DOCX
            docx_path = None
            if docx_name:
                docx_path = docx_dir / docx_name
            else:
                cand = docx_dir / f"{titulo}.docx"
                if cand.exists():
                    docx_path = cand

            # PDF
            pdf_path = pdf_dir / pdf_name if pdf_name else (pdf_dir / f"{titulo}.pdf")

            # IMG
            img_path = img_dir / img_name if img_name else (img_dir / f"{titulo}.png")

            if opt["dry_run"]:
                self.stdout.write(f"[{pos}] DRY: {titulo} | ordem={artigo.ordem} | area={area_obj.nome} | autor={autor_nome}")
                ok += 1
                continue

            # salva (1x)
            artigo.save()

            # anexa arquivos (após ter slug definitivo)
            slug_final = artigo.slug

            if docx_path and docx_path.exists() and should_write(artigo.arquivo_word):
                with open(docx_path, "rb") as f:
                    artigo.arquivo_word.save(f"{slug_final}.docx", File(f), save=False)

            if pdf_path and pdf_path.exists() and should_write(artigo.arquivo_pdf):
                with open(pdf_path, "rb") as f:
                    artigo.arquivo_pdf.save(f"{slug_final}.pdf", File(f), save=False)

            if img_path and img_path.exists() and should_write(artigo.imagem_capa):
                ext = img_path.suffix.lower() or ".png"
                with open(img_path, "rb") as f:
                    artigo.imagem_capa.save(f"{slug_final}{ext}", File(f), save=False)

            artigo.save()
            ok += 1

        self.stdout.write(self.style.SUCCESS(f"\n✅ Concluído. Processados: {ok}/{len(items)}"))
