import csv
import re
import unicodedata
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

from docx import Document

from A_Lei_no_NT.models import Area, Artigo, Autor
from A_Lei_no_NT.utils import docx_para_html


# -----------------------------
# Helpers de compatibilidade (campos podem variar entre versões)
# -----------------------------

def first_attr_name(obj, names):
    for n in names:
        if hasattr(obj, n):
            return n
    return None


def set_first_attr(obj, names, value):
    n = first_attr_name(obj, names)
    if not n:
        return False
    setattr(obj, n, value)
    return True


def get_fieldfile(obj, names):
    n = first_attr_name(obj, names)
    if not n:
        return None, None
    return n, getattr(obj, n)


def normalize_key(s: str) -> str:
    s = s or ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    return s.strip()


def strip_sm_prefix(text: str) -> str:
    return re.sub(r"^\s*sm\s*\d+\w*\s+", "", text, flags=re.IGNORECASE).strip()


def looks_like_sm_title_line(text: str, titulo: str) -> bool:
    t = " ".join((text or "").split())
    if not re.match(r"^\s*sm\s*\d+", t, flags=re.IGNORECASE):
        return False
    return normalize_key(strip_sm_prefix(t)) == normalize_key(titulo)


def looks_like_author_line(text: str, autor_nome: str) -> bool:
    t = " ".join((text or "").split()).strip()
    if not t:
        return False
    if re.match(r"^autor\s*:\s*", t, flags=re.IGNORECASE):
        return True
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
    Remove, apenas no começo do HTML:
      - "Sm#### <título>" quando for repetição do título
      - linha de autor ("Autor: ..." / "1. Albino Marks" / "Albino Marks")
      - título repetido no primeiro bloco
    Se bs4 não estiver instalado, retorna o HTML original (sem quebrar o import).
    """
    if not html:
        return html

    try:
        from bs4 import BeautifulSoup
        from bs4.element import Tag
    except Exception:
        return html

    soup = BeautifulSoup(html, "html.parser")
    container = soup.body if soup.body else soup

    def top_blocks():
        blocks = []
        for node in list(container.contents):
            if isinstance(node, Tag) and node.name in ("p", "h1", "h2", "h3"):
                blocks.append(node)
        return blocks

    for _ in range(10):
        blocks = top_blocks()
        if not blocks:
            break
        first = blocks[0]
        txt = first.get_text(" ", strip=True)

        if not txt:
            first.decompose()
            continue
        if normalize_key(txt) == normalize_key(titulo):
            first.decompose()
            continue
        if looks_like_sm_title_line(txt, titulo):
            first.decompose()
            continue
        if autor_nome and looks_like_author_line(txt, autor_nome):
            first.decompose()
            continue

        break

    return container.decode_contents() if soup.body else str(soup)


def read_esboco_titles(esboco_file: Path):
    """
    ESBOÇO padrão:
      1ª linha: "ESBOÇO" (descartar)
      2ª linha: nome da área/série (guardar)
      3ª linha em diante: títulos dos artigos (ordem 1..N)

    IMPORTANTE:
      - o 1º artigo pode repetir o nome da área (isso é correto e NÃO é duplicação).
    """
    if esboco_file.suffix.lower() == ".txt":
        lines = [l.strip() for l in esboco_file.read_text(encoding="utf-8-sig", errors="replace").splitlines()]
        lines = [l for l in lines if l]
    else:
        doc = Document(str(esboco_file))
        lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]

    if lines and normalize_key(lines[0]).startswith("esboc"):
        lines = lines[1:]

    serie_title = lines[0].strip() if lines else None
    article_titles = lines[1:] if len(lines) >= 2 else []

    article_titles = [" ".join(t.split()).strip() for t in article_titles if t.strip()]
    return serie_title, article_titles


def find_esboco_file(series_dir: Path) -> Path | None:
    """
    Aceita:
      - ESBOCO.docx / ESBOÇO.docx
      - ESBOCO_YYYY-MM-DD.docx
      - ESBOCO_*.txt (legado)
    Se houver mais de um, escolhe o mais recente (data no nome > mtime).
    """
    cands = []
    patterns = [
        "ESBOCO*.docx", "ESBOÇO*.docx", "Esboco*.docx", "Esboço*.docx",
        "ESBOCO*.txt",  "ESBOÇO*.txt",  "Esboco*.txt",  "Esboço*.txt",
    ]
    for pat in patterns:
        cands.extend(series_dir.glob(pat))
    if not cands:
        return None

    def score(p: Path):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
        if m:
            return (m.group(1), 9999999999)
        try:
            return ("0000-00-00", int(p.stat().st_mtime))
        except Exception:
            return ("0000-00-00", 0)

    cands.sort(key=score, reverse=True)
    return cands[0]


def read_manifest_rows(path: Path):
    raw = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    raw = [l for l in raw if l.strip()]
    if not raw:
        return []
    delim = ";" if ";" in raw[0] else ","
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delim))


def get_first(row: dict, *keys: str) -> str:
    for k in keys:
        v = row.get(k)
        if v is None:
            continue
        v = str(v).strip()
        if v:
            return v
    return ""


def resolve_path(p: str, fallback_dir: Path) -> Path | None:
    if not p:
        return None
    cand = Path(p)
    if cand.exists():
        return cand
    name = cand.name
    if name:
        cand2 = fallback_dir / name
        if cand2.exists():
            return cand2
    return None


class Command(BaseCommand):
    help = "Importa/atualiza uma série a partir de manifest.csv + DOCX/PDF/IMG, obedecendo o ESBOÇO."

    def add_arguments(self, parser):
        parser.add_argument("--serie", required=True, help="Nome da série (pasta dentro de --base).")
        parser.add_argument("--base", default="Apenas_Local/anexos_filtrados/SERIES", help="Pasta base das séries.")
        parser.add_argument("--data-root", default=None, help="Pasta anexos_filtrados (equivale a --base <data-root>/SERIES).")
        parser.add_argument("--manifest", default="manifest.csv", help="Nome do manifest dentro da pasta da série.")
        parser.add_argument("--dry-run", action="store_true", help="Não grava no banco nem envia arquivos.")
        parser.add_argument("--limit", type=int, default=0, help="Processa no máximo N itens (0 = todos).")

        parser.add_argument("--autor", default="Pr. Albino Marks", help="Autor padrão da série.")
        parser.add_argument("--area", default=None, help="Nome da Area (default: usa --serie).")

        parser.add_argument(
            "--ordem-mode",
            default="esboco",
            choices=["esboco", "manifest", "compact", "offset"],
            help="Como definir Artigo.ordem: esboco (recomendado), manifest, compact, offset.",
        )
        parser.add_argument(
            "--offset-scope",
            default="area",
            choices=["area", "global"],
            help="Quando ordem-mode=offset: base do offset vem do max(ordem) da area ou global.",
        )
        parser.add_argument("--overwrite-media", action="store_true", help="Reenvia mídia mesmo se já existir.")
        parser.add_argument("--no-clean-html", action="store_true", help="Não limpa duplicações no HTML.")
        parser.add_argument("--include-non-ok", action="store_true", help="Inclui status != OK (DUVIDOSO/FALTANDO).")

    def handle(self, *args, **opt):
        serie = opt["serie"].strip()
        base = (Path(opt["data_root"]).resolve() / "SERIES") if opt.get("data_root") else Path(opt["base"]).resolve()
        series_dir = (base / serie).resolve()

        manifest_path = series_dir / opt["manifest"]
        if not manifest_path.exists():
            raise SystemExit(f"Não achei manifest: {manifest_path}")
        autor_nome = opt["autor"] or "Pr. Albino Marks"

        area_nome = opt["area"] or serie

        area_obj, _ = Area.objects.get_or_create(nome=area_nome, defaults={"visivel": True})
        autor_obj, _ = Autor.objects.get_or_create(nome=autor_nome)

        esboco_file = find_esboco_file(series_dir)
        esboco_orders = {}  # key -> [ordens...]
        if esboco_file and opt["ordem_mode"] == "esboco":
            serie_title, titles = read_esboco_titles(esboco_file)
            if serie_title:
                self.stdout.write(f"📌 Área (linha 2 do ESBOÇO): {serie_title}")

            # titles já começa na 3ª linha do ESBOÇO.
            # NÃO remove o 1º artigo mesmo que ele repita o nome da área.
            for idx, t in enumerate(titles, start=1):
                k = normalize_key(t)
                esboco_orders.setdefault(k, []).append(idx)

        items = read_manifest_rows(manifest_path)

        if not opt["include_non_ok"]:
            filtered = []
            for r in items:
                status = get_first(r, "status", "Status", "STATUS").upper()
                if not status:
                    filtered.append(r)
                elif status == "OK":
                    filtered.append(r)
            items = filtered

        if opt["limit"] and opt["limit"] > 0:
            items = items[: opt["limit"]]

        self.stdout.write(self.style.SUCCESS(f"Importando {len(items)} itens da série '{serie}'..."))
        self.stdout.write(f"📄 manifest: {manifest_path.name}")
        if esboco_file and opt["ordem_mode"] == "esboco":
            self.stdout.write(f"✅ Ordem vinda do ESBOÇO: {esboco_file.name}")
        else:
            self.stdout.write(f"ℹ️ Ordem-mode: {opt['ordem_mode']}")

        base_offset = 0
        if opt["ordem_mode"] == "offset":
            qs = Artigo.objects.all()
            if opt["offset_scope"] == "area":
                qs = qs.filter(area=area_obj)
            base_offset = qs.aggregate(m=models.Max("ordem"))["m"] or 0

        docx_dir = series_dir / "DOCX"
        pdf_dir = series_dir / "PDF"
        img_dir = series_dir / "IMG"
        html_dir = series_dir / "HTML"  # opcional

        index_docx = {normalize_key(p.stem): p for p in docx_dir.glob("*.docx")}
        index_pdf = {normalize_key(p.stem): p for p in pdf_dir.glob("*.pdf")}
        index_img = {
            normalize_key(p.stem): p
            for p in img_dir.glob("*")
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        }

        def should_write(field):
            if opt["overwrite-media"]:
                return True
            if not field:
                return True
            try:
                return not field.storage.exists(field.name)
            except Exception:
                return False

        ok = 0
        for pos, row in enumerate(items, start=1):
            titulo = get_first(row, "titulo_esboco", "titulo", "title").strip()
            if not titulo:
                self.stdout.write(self.style.WARNING(f"[{pos}] ⚠️ Sem título no manifest, pulando."))
                continue

            slug = get_first(row, "slug")

            ordem = None
            if opt["ordem_mode"] == "esboco" and esboco_orders:
                k = normalize_key(titulo)
                lst = esboco_orders.get(k) or []
                ordem = lst.pop(0) if lst else None
            elif opt["ordem_mode"] == "manifest":
                try:
                    ordem = int(get_first(row, "ordem") or 0) or None
                except Exception:
                    ordem = None
            elif opt["ordem_mode"] == "compact":
                ordem = pos
            elif opt["ordem_mode"] == "offset":
                ordem = base_offset + pos

            artigo = None
            if slug:
                artigo = Artigo.objects.filter(slug=slug).first()
            if artigo is None:
                artigo = Artigo.objects.filter(titulo__iexact=titulo, area=area_obj).first()

            if artigo is None:
                artigo = Artigo(titulo=titulo)
                if slug:
                    artigo.slug = slug

            html = ""
            html_path = html_dir / f"{titulo}.html"
            if html_path.exists():
                html = html_path.read_text(encoding="utf-8", errors="replace")
            else:
                docx_path = resolve_path(get_first(row, "destino_docx", "origem_docx"), docx_dir)
                if docx_path is None:
                    docx_name = get_first(row, "docx")
                    if docx_name:
                        cand = docx_dir / docx_name
                        if cand.exists():
                            docx_path = cand
                if docx_path is None:
                    docx_path = index_docx.get(normalize_key(titulo))

                if docx_path and docx_path.exists():
                    out = docx_para_html(str(docx_path))
                    html = out[0] if isinstance(out, (tuple, list)) else (out or "")
                else:
                    self.stdout.write(self.style.WARNING(f"[{pos}] ⚠️ Sem HTML e sem DOCX: {titulo}"))
                    html = ""

            if html and not opt["no_clean_html"]:
                html = clean_html_leading_noise(html, titulo=titulo, autor_nome=autor_nome)

            artigo.titulo = titulo
            artigo.area = area_obj
            artigo.autor = autor_obj
            if ordem is not None:
                artigo.ordem = ordem
            if html:
                set_first_attr(artigo, ["conteudo_html", "conteudo", "html", "conteudoHtml"], html)
            if not artigo.publicado_em:
                artigo.publicado_em = timezone.now()

            docx_path = resolve_path(get_first(row, "destino_docx", "origem_docx"), docx_dir) or index_docx.get(normalize_key(titulo))
            pdf_path = index_pdf.get(normalize_key(titulo))
            img_path = index_img.get(normalize_key(titulo))

            pdf_name = get_first(row, "pdf")
            if pdf_name:
                cand = pdf_dir / pdf_name
                if cand.exists():
                    pdf_path = cand

            img_name = get_first(row, "imagem", "image")
            if img_name:
                cand = img_dir / img_name
                if cand.exists():
                    img_path = cand

            if opt["dry_run"]:
                self.stdout.write(f"[{pos}] DRY: {titulo} | ordem={ordem} | area={area_obj.nome} | autor={autor_nome}")
                ok += 1
                continue

            artigo.save()
            slug_final = artigo.slug

            word_attr, word_ff = get_fieldfile(artigo, ["arquivo_word", "arquivo_docx", "docx", "arquivo_wordfile"])

            if docx_path and docx_path.exists() and word_ff is not None and should_write(word_ff):
                with open(docx_path, "rb") as f:
                    getattr(artigo, word_attr).save(f"{slug_final}.docx", File(f), save=False)

            pdf_attr, pdf_ff = get_fieldfile(artigo, ["arquivo_pdf", "pdf", "arquivo_pdffile"])

            if pdf_path and pdf_path.exists() and pdf_ff is not None and should_write(pdf_ff):
                with open(pdf_path, "rb") as f:
                    getattr(artigo, pdf_attr).save(f"{slug_final}.pdf", File(f), save=False)

            img_attr, img_ff = get_fieldfile(artigo, ["imagem_capa", "imagem", "capa", "imagem_principal"])

            if img_path and img_path.exists() and img_ff is not None and should_write(img_ff):
                ext = img_path.suffix.lower() or ".png"
                with open(img_path, "rb") as f:
                    getattr(artigo, img_attr).save(f"{slug_final}{ext}", File(f), save=False)

            artigo.save()
            ok += 1

        self.stdout.write(self.style.SUCCESS(f"\n✅ Concluído. Processados: {ok}/{len(items)}"))
