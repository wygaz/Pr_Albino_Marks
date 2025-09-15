from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from A_Lei_no_NT.models import Artigo
from A_Lei_no_NT import utils

class Command(BaseCommand):
    help = (
        "Gera PDFs faltantes em static/pdfs/<slug>.pdf a partir dos DOCX "
        "(localmente). Usa docx2pdf no Windows. "
        "Opções: --dry-run, --overwrite, --slug=<parte-do-slug>, --limit=N."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Só mostra o que faria; não gera arquivos.")
        parser.add_argument("--overwrite", action="store_true",
                            help="Se já existir PDF, sobrescreve.")
        parser.add_argument("--slug", default="", help="Filtra por parte do slug.")
        parser.add_argument("--limit", type=int, default=0,
                            help="Gera no máximo N PDFs (0 = sem limite).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        overwrite = opts["overwrite"]
        slug_filter = (opts["slug"] or "").strip().lower()
        limit = int(opts["limit"] or 0)

        base_dir = Path(settings.BASE_DIR)
        pdf_dir = base_dir / "static" / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)

        # tenta importar docx2pdf
        converter = None
        try:
            from docx2pdf import convert as _docx2pdf_convert
            converter = ("docx2pdf", _docx2pdf_convert)
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                "docx2pdf não disponível. Instale com: pip install docx2pdf "
                "(requer Microsoft Word no Windows)."
            ))
            converter = None

        qs = Artigo.objects.all().order_by("id")
        total = gerados = pulados = faltando_docx = 0

        for a in qs:
            slug_alvo = slugify((a.slug or utils.limpar_numeracao(a.titulo or ""))[:90])
            if slug_filter and slug_filter not in slug_alvo:
                continue

            total += 1
            pdf_path = pdf_dir / f"{slug_alvo}.pdf"
            if pdf_path.exists() and not overwrite:
                pulados += 1
                self.stdout.write(self.style.NOTICE(
                    f"[{a.id}] {slug_alvo}  — PDF já existe, pulei (use --overwrite para refazer)."
                ))
                continue

            # localizar DOCX (novo ou legados)
            docx_path = utils.localizar_docx(slug_alvo)
            if not docx_path:
                faltando_docx += 1
                self.stdout.write(self.style.WARNING(
                    f"[{a.id}] {slug_alvo}  — DOCX não encontrado para gerar PDF."
                ))
                continue

            self.stdout.write(f"[{a.id}] {slug_alvo}  ->  {pdf_path.name}")

            if dry:
                continue

            # cria pasta e remove destino se overwrite
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            if overwrite:
                pdf_path.unlink(missing_ok=True)

            ok = False

            # 1) tentar docx2pdf (Word)
            if converter and converter[0] == "docx2pdf":
                try:
                    converter[1](docx_path.as_posix(), pdf_path.as_posix())
                    ok = pdf_path.exists() and pdf_path.stat().st_size > 0
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"   docx2pdf falhou: {e!s}"))

            # 2) fallback: LibreOffice (soffice) se Word falhar
            if not ok:
                from shutil import which
                soffice = which("soffice") or "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
                try:
                    import subprocess
                    if (Path(soffice).exists() or which("soffice")):
                        subprocess.run([
                            soffice, "--headless", "--convert-to", "pdf",
                            "--outdir", pdf_path.parent.as_posix(), docx_path.as_posix()
                        ], check=True)
                        ok = pdf_path.exists() and pdf_path.stat().st_size > 0
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   LibreOffice falhou: {e!s}"))

            if not ok:
                self.stdout.write(self.style.ERROR(
                    "   Falha ao gerar PDF. Feche diálogos do Word (ou instale LibreOffice) "
                    "ou gere manualmente em static/pdfs/<slug>.pdf."
                ))
                continue

            gerados += 1
            self.stdout.write(self.style.SUCCESS(f"   ✓ PDF gerado: {pdf_path}"))


        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Resumo"))
        self.stdout.write(f"Selecionados: {total} | Gerados: {gerados} | Pulados (já existiam): {pulados} | Sem DOCX: {faltando_docx}")
        self.stdout.write(self.style.NOTICE(f"Dry-run: {dry}  | Overwrite: {overwrite}"))
