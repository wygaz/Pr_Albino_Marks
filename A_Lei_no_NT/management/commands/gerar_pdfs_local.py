from django.core.management.base import BaseCommand
from django.conf import settings
from A_Lei_no_NT.models import Artigo
import os
import pythoncom

class Command(BaseCommand):
    help = "Gera PDFs localmente no Windows via Microsoft Word (COM) e atualiza 'arquivo_pdf'."

    def add_arguments(self, parser):
        parser.add_argument("--ids", nargs="+", type=int, help="IDs específicos de artigos (opcional)")

    def handle(self, *args, **opts):
        # Inicializa COM de forma segura para uso em management command
        pythoncom.CoInitialize()

        try:
            import win32com.client
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                "pywin32 não disponível. Instale com: pip install pywin32"
            ))
            return

        Word = win32com.client.Dispatch("Word.Application")
        Word.Visible = False

        if opts.get("ids"):
            qs = Artigo.objects.filter(pk__in=opts["ids"])
        else:
            qs = Artigo.objects.exclude(arquivo_word="")

        base_pdf_dir = os.path.join(settings.MEDIA_ROOT, "pdfs", "artigos")
        os.makedirs(base_pdf_dir, exist_ok=True)

        ok = 0
        fail = 0
        for art in qs:
            try:
                docx_path = art.arquivo_word.path  # ex: C:\...\media\uploads\os-escritores-...docx
                if not os.path.exists(docx_path):
                    self.stderr.write(f"[skip] DOCX não encontrado: {docx_path}")
                    continue

                # Nome do PDF pelo slug
                pdf_name = f"{art.slug or 'sem-slug'}.pdf"
                pdf_abs  = os.path.join(base_pdf_dir, pdf_name)

                # Converte via Word (17 = wdFormatPDF)
                doc = Word.Documents.Open(docx_path)
                doc.SaveAs(pdf_abs, FileFormat=17)
                doc.Close()

                # Atualiza o FileField (caminho relativo a MEDIA_ROOT)
                rel = os.path.join("pdfs", "artigos", pdf_name).replace("\\", "/")
                if art.arquivo_pdf.name != rel:
                    art.arquivo_pdf.name = rel
                    art.save(update_fields=["arquivo_pdf"])

                self.stdout.write(self.style.SUCCESS(f"[OK] {art.pk} – {art.titulo}"))
                ok += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"[ERRO] {art.pk} – {art.titulo}: {e}"))
                fail += 1

        Word.Quit()
        pythoncom.CoUninitialize()

        self.stdout.write(self.style.SUCCESS(f"Concluído. OK: {ok}, Falhas: {fail}"))
