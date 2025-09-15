# A_Lei_no_NT/management/commands/regerar_pdfs_artigos.py
from django.core.management.base import BaseCommand
from A_Lei_no_NT.models import Artigo

class Command(BaseCommand):
    help = "(Re)gera o PDF de todos os artigos que possuem arquivo_word"

    def handle(self, *args, **options):
        ok = 0
        fail = 0
        for art in Artigo.objects.exclude(arquivo_word=""):
            try:
                art._ensure_pdf_from_docx()
                ok += 1
            except Exception as e:
                self.stderr.write(f"Falha em {art.pk} – {art.titulo}: {e}")
                fail += 1
        self.stdout.write(self.style.SUCCESS(f"Pronto. OK: {ok}, Falhas: {fail}"))
