import csv
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from A_Lei_no_NT import utils
from A_Lei_no_NT.models import Artigo, Autor


def read_manifest_rows(path: Path):
    """
    Lê manifest.csv em 3 cenários comuns:
    1) CSV normal com ; (padrão do seu pipeline)
    2) CSV normal com ,
    3) "linha inteira entre aspas":  "a;b;c;d"
    """
    raw = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    raw = [l for l in raw if l.strip()]
    if not raw:
        return []

    # caso "linha inteira entre aspas": "a;b;c"
    first = raw[0].strip()
    if first.startswith('"') and first.endswith('"') and ";" in first:
        def unq(s: str) -> str:
            s = s.strip()
            return s[1:-1] if s.startswith('"') and s.endswith('"') else s

        raw = [unq(l) for l in raw]
        header = raw[0].split(";")
        rows = []
        for line in raw[1:]:
            parts = line.split(";")
            if len(parts) < len(header):
                parts += [""] * (len(header) - len(parts))
            rows.append(dict(zip(header, parts[: len(header)])))
        return rows

    # CSV normal
    delim = ";" if ";" in raw[0] else ","
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delim))


def get_first(r: dict, *keys: str) -> str:
    for k in keys:
        if k in r and r.get(k) is not None:
            v = str(r.get(k)).strip()
            if v:
                return v
    return ""


def get_status(r: dict) -> str:
    return get_first(r, "status", "Status", "STATUS").strip().upper()


def to_int(v, default=0) -> int:
    try:
        return int(str(v).strip())
    except Exception:
        return default


class Command(BaseCommand):
    help = "Importa uma série do Apenas_Local/anexos_filtrados/SERIES/<SERIE> usando manifest.csv"

    def add_arguments(self, parser):
        parser.add_argument("--serie", required=True, help="Nome da pasta da série (exatamente como está em SERIES/)")
        parser.add_argument("--dry-run", action="store_true", help="Só mostra o que faria; não altera nada.")
        parser.add_argument("--update", action="store_true", help="Se já existir artigo, atualiza conteúdo/arquivos.")
        parser.add_argument("--overwrite-files", action="store_true", help="Sobrescreve PDF/IMG/DOCX se já existirem.")
        parser.add_argument("--limit", type=int, default=0, help="Processa no máximo N itens (0=sem limite).")

    def handle(self, *args, **opts):
        serie = opts["serie"]
        dry = opts["dry_run"]
        do_update = opts["update"]
        overwrite_files = opts["overwrite_files"]
        limit = int(opts["limit"] or 0)

        base_series = Path(settings.BASE_DIR) / "Apenas_Local" / "anexos_filtrados" / "SERIES"
        series_dir = base_series / serie
        manifest_path = series_dir / "manifest.csv"

        if not series_dir.exists():
            raise SystemExit(f"Série não encontrada: {series_dir}")
        if not manifest_path.exists():
            raise SystemExit(f"manifest.csv não encontrado: {manifest_path}")

        docx_dir = series_dir / "DOCX"
        pdf_dir = series_dir / "PDF"
        img_dir = series_dir / "IMG"

        static_pdf_dir = Path(settings.BASE_DIR) / "static" / "pdfs"
        static_pdf_dir.mkdir(parents=True, exist_ok=True)

        media_root = Path(settings.MEDIA_ROOT)
        media_docx_dir = media_root / "uploads"
        media_img_dir = media_root / "imagens" / "artigos"
        media_docx_dir.mkdir(parents=True, exist_ok=True)
        media_img_dir.mkdir(parents=True, exist_ok=True)

        def unique_slug(base: str) -> str:
            base = (base or "").strip()[:90]
            s = slugify(base)[:90] or "artigo"
            cand = s
            i = 2
            while Artigo.objects.filter(slug=cand).exists():
                cand = f"{s}-{i}"
                i += 1
            return cand

        rows = read_manifest_rows(manifest_path)

        # só OK
        rows = [r for r in rows if get_status(r) == "OK"]

        if limit and limit > 0:
            rows = rows[:limit]

        self.stdout.write(self.style.NOTICE(f"Importando {len(rows)} itens da série '{serie}'..."))

        ok = skipped = fail = 0

        for r in rows:
            # campos (compatível com manifest antigo e novo)
            ordem = to_int(get_first(r, "ordem", "ordem_esboco", "n", "N"), 0)
            titulo = get_first(r, "titulo_esboco", "titulo_normalizado", "titulo", "TITULO")
            docx_match = get_first(r, "docx_match", "docx", "DOCX")
            destino_docx = get_first(r, "destino_docx", "path_docx", "caminho_docx")

            # localizar DOCX
            if destino_docx:
                docx_path = Path(destino_docx)
            else:
                docx_path = (docx_dir / docx_match) if docx_match else (docx_dir / f"{titulo}.docx")

            if not docx_path.exists():
                self.stdout.write(self.style.WARNING(f"[{ordem}] DOCX ausente: {docx_path}"))
                fail += 1
                continue

            # slug / artigo existente
            artigo = Artigo.objects.filter(titulo__iexact=titulo).first()
            if artigo and not do_update:
                self.stdout.write(self.style.NOTICE(f"[{ordem}] Já existe (skip): {titulo}"))
                skipped += 1
                continue

            slug = artigo.slug if artigo else unique_slug(titulo)

            # gerar HTML + autor (sem depender do título do docx)
            try:
                html, _titulo_extraido, autor_nome = utils.docx_para_html(docx_path.as_posix())
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{ordem}] Falha ao ler DOCX '{docx_path.name}': {e}"))
                fail += 1
                continue

            autor_obj = None
            if autor_nome:
                autor_obj, _ = Autor.objects.get_or_create(nome=autor_nome.strip())

            # localizar PDF por match/por título
            pdf_match = get_first(r, "pdf_match", "pdf", "PDF")
            pdf_src = (pdf_dir / pdf_match) if pdf_match else (pdf_dir / f"{titulo}.pdf")
            pdf_dst = static_pdf_dir / f"{slug}.pdf"

            # localizar IMG por match/por título
            img_match = get_first(r, "imagem_match", "img_match", "imagem", "IMG")
            img_src = (img_dir / img_match) if img_match else None
            if img_src and not img_src.exists():
                img_src = None

            if img_src is None:
                for ext in (".png", ".jpg", ".jpeg", ".webp"):
                    cand = img_dir / f"{titulo}{ext}"
                    if cand.exists():
                        img_src = cand
                        break

            # definir destinos (aqui só calcula, NÃO copia)
            docx_dst = media_docx_dir / f"{slug}.docx"
            img_dst = (media_img_dir / f"{slug}{img_src.suffix.lower()}") if img_src is not None else None

            self.stdout.write(f"[{ordem}] {titulo}  -> slug={slug}")

            if dry:
                continue

            # cria/atualiza artigo
            if not artigo:
                artigo = Artigo(titulo=titulo, slug=slug, publicado_em=timezone.now(), ordem=ordem)

            artigo.conteudo_html = html
            # evita warning do Pylance e mantém correto no Django

            setattr(artigo, "autor_id", autor_obj.pk if autor_obj else None)
            artigo.ordem = ordem
            artigo.save()

            # copiar DOCX
            if overwrite_files or not docx_dst.exists():
                shutil.copy2(docx_path, docx_dst)
            artigo.arquivo_word.name = f"uploads/{docx_dst.name}"

            # copiar IMG (AGORA sim: artigo existe e não é dry-run)
            if img_src is not None and img_dst is not None:
                if overwrite_files or not img_dst.exists():
                    shutil.copy2(img_src, img_dst)
                artigo.imagem_capa.name = f"imagens/artigos/{img_dst.name}"

            # salva os campos de arquivo (só atualiza o que existir)
            update_fields = ["arquivo_word"]
            if img_src is not None and img_dst is not None:
                update_fields.append("imagem_capa")
            artigo.save(update_fields=update_fields)

            # copiar PDF (se existir)
            if pdf_src.exists():
                if overwrite_files or not pdf_dst.exists():
                    shutil.copy2(pdf_src, pdf_dst)
            else:
                self.stdout.write(self.style.WARNING(f"    PDF não encontrado (ok, pode gerar depois): {pdf_src.name}"))

            ok += 1

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Resumo"))
        self.stdout.write(f"OK: {ok} | Skipped: {skipped} | Falhas: {fail}")
        self.stdout.write(self.style.NOTICE(
            "Dica: depois rode 'python manage.py auditar_consistencia_artigos --fix' e confira os PDFs em static/pdfs/."
        ))
