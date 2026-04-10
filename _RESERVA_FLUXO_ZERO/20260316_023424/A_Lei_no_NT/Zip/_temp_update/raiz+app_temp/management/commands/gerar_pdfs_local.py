"""
gerar_pdfs_local.py  –  Management command Django

USO LOCAL — CUIDADO: ATUALIZA BANCO E STORAGE.

Descrição:
    Converte DOCX → PDF usando Microsoft Word (COM/pywin32) e atualiza o campo
    'arquivo_pdf' do modelo Artigo. Baixa o DOCX a partir do campo 'arquivo_word'
    (default_storage) e envia o PDF gerado para o mesmo storage
    (ex.: S3 ou FileSystemStorage em 'pdfs/artigos/<slug>.pdf').

Quando usar:
    • Depois que o artigo já foi criado/publicado e o campo 'arquivo_word'
      está preenchido com o DOCX no storage (S3 ou pasta media).
    • Ideal para gerar/atualizar PDFs em lote a partir dos DOCXs já armazenados.

Pré-requisitos:
    • Windows + Microsoft Word instalado.
    • 'pywin32' (pythoncom / win32com) disponível.
    • default_storage acessível (atenção: pode apontar para S3 de PRODUÇÃO).

Efeitos colaterais:
    • Grava/atualiza PDFs em 'pdfs/artigos/<slug>.pdf' no storage.
    • Atualiza o campo 'arquivo_pdf' no banco de dados.

Segurança:
    • Executar APENAS em ambiente local com DEBUG=True.
    • NÃO executar em produção sem revisar o apontamento de BD/storage.

Exemplos:
    python manage.py gerar_pdfs_local --ids 10 12 15
    python manage.py gerar_pdfs_local
"""


from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from A_Lei_no_NT.models import Artigo
from A_Lei_no_NT.utils_storage import open_file
import os
import pythoncom
import tempfile
from django.core.management.base import CommandError

if not settings.DEBUG:
    raise CommandError("Desabilitado em produção. Use apenas em ambiente local (DEBUG=True).")

class Command(BaseCommand):
    help = "Gera PDFs localmente no Windows via Microsoft Word (COM) e atualiza 'arquivo_pdf'."

    def add_arguments(self, parser):
        parser.add_argument("--ids", nargs="+", type=int, help="IDs específicos de artigos (opcional)")

    def handle(self, *args, **opts):
        # Inicializa COM (obrigatório em management command)
        pythoncom.CoInitialize()

        try:
            import win32com.client
        except Exception:
            self.stderr.write(self.style.ERROR("pywin32 não disponível. Instale com: pip install pywin32"))
            pythoncom.CoUninitialize()
            return

        Word = win32com.client.Dispatch("Word.Application")
        Word.Visible = False

        qs = Artigo.objects.filter(pk__in=opts["ids"]) if opts.get("ids") else Artigo.objects.exclude(arquivo_word="")

        ok = 0
        fail = 0
        for art in qs:
            if not art.arquivo_word:
                continue

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_docx = os.path.join(tmpdir, "entrada.docx")
                tmp_pdf  = os.path.join(tmpdir, "saida.pdf")

                # Baixa DOCX do storage
                try:
                    with open_file(art.arquivo_word, "rb") as src, open(tmp_docx, "wb") as dst:
                        dst.write(src.read())
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"[ERRO] {art.pk} – baixar DOCX: {e}"))
                    fail += 1
                    continue

                try:
                    # Converte via Word (17 = wdFormatPDF)
                    doc = Word.Documents.Open(tmp_docx)
                    doc.SaveAs(tmp_pdf, FileFormat=17)
                    doc.Close()

                    if not os.path.exists(tmp_pdf):
                        raise RuntimeError("PDF não foi gerado pelo Word.")

                    # Sobe para o storage
                    pdf_name = f"{art.slug or 'sem-slug'}.pdf"
                    rel = os.path.join("pdfs", "artigos", pdf_name).replace("\\", "/")
                    with open(tmp_pdf, "rb") as f:
                        default_storage.save(rel, ContentFile(f.read()))

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
