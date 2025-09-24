# A_Lei_no_NT/management/commands/gerar_pdf_local_salvar_na_Producao.py
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from A_Lei_no_NT.models import Artigo
from A_Lei_no_NT.utils_storage import open_file
import subprocess
import shutil
import os
from tempfile import NamedTemporaryFile

class Command(BaseCommand):
    help = (
        "Gera PDF localmente a partir do DOCX e salva no storage configurado "
        "(S3 quando USE_S3=1). Use --slug <slug> ou --all. --force para sobrescrever."
    )

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Slug do artigo específico")
        parser.add_argument("--all", action="store_true", help="Processar todos os artigos visíveis com DOCX")
        parser.add_argument("--force", action="store_true", help="Sobrescrever PDF existente")

    def handle(self, *args, **opts):
        slug = opts.get("slug")
        all_flag = opts.get("all")
        force = opts.get("force", False)

        # Verificação amigável do ambiente de storage
        use_s3 = str(getattr(settings, "USE_S3", "0")).lower() in ("1", "true", "yes")
        soffice = getattr(settings, "LIBREOFFICE_PATH", "soffice")

        if not slug and not all_flag:
            self.stderr.write("⚠️  Informe --slug <slug> ou --all")
            return

        if not shutil.which(soffice) and not os.path.isfile(soffice):
            self.stderr.write(
                f"❌ LibreOffice não encontrado. Ajuste LIBREOFFICE_PATH (atual: {soffice}) "
                "no seu .env.<ENV_NAME>."
            )
            return

        if not use_s3:
            self.stdout.write(
                self.style.WARNING(
                    "AVISO: USE_S3 está desativado (USE_S3=0). O PDF será salvo no storage local. "
                    "Se deseja salvar no S3 de produção, rode com um .env que tenha USE_S3=1 "
                    "(ex.: .env.remote_s3/.env.prod)."
                )
            )

        qs = Artigo.objects.filter(visivel=True)
        if slug:
            qs = qs.filter(slug=slug)

        # Filtra apenas quem tem DOCX
        qs = qs.exclude(arquivo_word="").exclude(arquivo_word__isnull=True)

        if not qs.exists():
            if slug:
                self.stderr.write(self.style.ERROR(f"❌ Nenhum artigo encontrado para slug '{slug}' com DOCX."))
            else:
                self.stderr.write(self.style.ERROR("❌ Não há artigos visíveis com DOCX para processar."))
            return

        processados = 0
        for art in qs.order_by("ordem", "titulo"):
            try:
                if art.arquivo_pdf and not force:
                    self.stdout.write(f"⏩ {art.slug}: já possui PDF. Use --force para sobrescrever.")
                    continue

                # 1) Baixa o DOCX do storage para arquivo temporário local
                with open_file(art.arquivo_word, "rb") as src, \
                     NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
                    shutil.copyfileobj(src, tmp_docx)
                    tmp_docx_path = tmp_docx.name

                # 2) Converte via LibreOffice para PDF (em diretório temporário)
                with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    tmp_pdf_dir = os.path.dirname(tmp_pdf.name)
                    # Na conversão, o LibreOffice ignora o nome do tmp_pdf;
                    # ele gera <nome_docx>.pdf dentro de --outdir.
                    tmp_pdf_base = os.path.splitext(os.path.basename(tmp_docx_path))[0] + ".pdf"

                # Executa conversão
                # obs: chamar com lista evita problemas de aspas em caminhos com espaços
                subprocess.check_call([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp_pdf_dir, tmp_docx_path])

                pdf_path = os.path.join(tmp_pdf_dir, tmp_pdf_base)
                if not os.path.exists(pdf_path):
                    raise FileNotFoundError(f"Conversão não gerou o PDF esperado: {pdf_path}")

                # 3) Lê o PDF gerado e salva no storage via FileField.save(...)
                with open(pdf_path, "rb") as fpdf:
                    pdf_bytes = fpdf.read()

                # Nome final do arquivo no storage
                nome_pdf = f"{art.slug}.pdf"
                art.arquivo_pdf.save(nome_pdf, ContentFile(pdf_bytes), save=True)

                # 4) Limpeza dos temporários
                try:
                    os.remove(tmp_docx_path)
                except Exception:
                    pass
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass

                processados += 1
                destino = "S3" if use_s3 else "storage local"
                self.stdout.write(self.style.SUCCESS(f"✅ {art.slug}: PDF gerado e salvo no {destino}."))
            except Artigo.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"❌ Artigo {art.slug} não encontrado."))
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR(f"❌ {art.slug}: erro na conversão pelo LibreOffice ({e})."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ {art.slug}: erro: {e}"))

        self.stdout.write(self.style.HTTP_INFO(f"Concluído. PDFs processados: {processados}."))
