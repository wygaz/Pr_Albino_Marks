import os
import subprocess
import sys
import tempfile
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Max
from django.db import models
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

from A_Lei_no_NT.utils import docx_para_html, gerar_slug
from A_Lei_no_NT.utils_storage import open_file

def caminho_pdf(instance, filename):
    # mantemos apenas a pasta; o nome final será pelo slug
    return f"pdfs/artigos/{filename}"

class Artigo(models.Model):
    titulo = models.CharField(max_length=255)  # (não nulo)
    slug = models.SlugField(max_length=100, unique=True)  # agora sem null/blank
#   slug = models.SlugField(max_length=100, unique=True, db_index=True)
    conteudo_html = models.TextField(null=True, blank=True)
    imagem_capa = models.ImageField(upload_to="imagens/artigos/", null=True, blank=True)
    arquivo_word = models.FileField(upload_to="uploads/artigos/", null=True, blank=True)
    arquivo_pdf = models.FileField(upload_to=caminho_pdf, null=True, blank=True)
    publicado_em = models.DateTimeField(null=True, blank=True)
    ordem = models.IntegerField(null=True, blank=True)
    visivel = models.BooleanField(default=True)

    autor = models.ForeignKey('Autor', on_delete=models.SET_NULL, null=True, blank=True)
    area = models.ForeignKey('Area', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # 1) Extrair HTML/título/autor do DOCX, se aplicável
        if self.arquivo_word and not self.conteudo_html:
            html, titulo_extraido, autor_detectado = docx_para_html(self.arquivo_word)
            self.conteudo_html = html
            if not self.titulo:
                self.titulo = (titulo_extraido or "").strip()
            if autor_detectado:
                autor_obj, _ = Autor.objects.get_or_create(nome=autor_detectado)
                self.autor = autor_obj

        # 2) Slug único
        if not self.slug and self.titulo:
            base = gerar_slug(self.titulo)
            slug = base
            i = 1
            while Artigo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug

        # 3) Datas e ordem
        if not self.publicado_em:
            self.publicado_em = timezone.now()
        if self.ordem is None:
            maior = Artigo.objects.aggregate(Max('ordem'))['ordem__max'] or 0
            self.ordem = maior + 1

        super().save(*args, **kwargs)  # salva para garantir PK

        # 4) Renomear imagem de capa pelo slug (S3-safe)
        if self.imagem_capa:
            old_name = self.imagem_capa.name
            ext = os.path.splitext(old_name)[1]
            novo_nome = f"{self.slug}{ext}"
            novo_rel = f"imagens/artigos/{novo_nome}"
            if not old_name.endswith(novo_nome):
                try:
                    if default_storage.exists(novo_rel):
                        default_storage.delete(novo_rel)
                    with open_file(old_name, "rb") as src:
                        default_storage.save(novo_rel, src)
                    if default_storage.exists(old_name):
                        default_storage.delete(old_name)
                    self.imagem_capa.name = novo_rel
                    super().save(update_fields=["imagem_capa"])
                except Exception as e:
                    print(f"⚠️ Erro ao renomear imagem de capa: {e}")

        # 5) Gerar/atualizar PDF a partir do DOCX se necessário (S3-safe)
        if self.arquivo_word:
            self._ensure_pdf_from_docx()

    def _ensure_pdf_from_docx(self):
        """
        Gera (ou regenera) o PDF baseado no arquivo_word.
        • Linux: tenta LibreOffice headless
        • Windows/macOS: tenta docx2pdf (se instalado)
        """
        if not self.arquivo_word:
            return

        pdf_filename = f"{self.slug}.pdf" if self.slug else "temp.pdf"
        pdf_rel = os.path.join("pdfs", "artigos", pdf_filename).replace("\\", "/")

        # Se já existe no storage, apenas garante o apontamento
        if default_storage.exists(pdf_rel):
            if self.arquivo_pdf.name != pdf_rel:
                self.arquivo_pdf.name = pdf_rel
                super().save(update_fields=["arquivo_pdf"])
            return

        ok = False
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_docx = os.path.join(tmpdir, "entrada.docx")
            # baixa DOCX do storage para temp local
            try:
                with open_file(self.arquivo_word, "rb") as src, open(tmp_docx, "wb") as dst:
                    dst.write(src.read())
            except Exception as e:
                print("⚠️ Não foi possível baixar o DOCX do storage:", e)
                return

            tmp_pdf = os.path.join(tmpdir, "saida.pdf")

            # 1) Linux / LibreOffice
            if sys.platform.startswith("linux"):
                try:
                    subprocess.run(
                        ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir",
                         tmpdir, tmp_docx],
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    # LO tende a gerar <base>.pdf no tmpdir
                    base_pdf = os.path.splitext(tmp_docx)[0] + ".pdf"
                    if os.path.exists(base_pdf):
                        os.replace(base_pdf, tmp_pdf)
                    ok = os.path.exists(tmp_pdf)
                except Exception as e:
                    print("⚠️ LibreOffice não funcionou:", e)

            # 2) Fallback: docx2pdf (Windows/macOS)
            if not ok:
                try:
                    from docx2pdf import convert as docx2pdf_convert
                    docx2pdf_convert(tmp_docx, tmp_pdf)
                    ok = os.path.exists(tmp_pdf)
                except Exception as e:
                    print("⚠️ docx2pdf indisponível:", e)

            # 3) Sobe PDF gerado ao storage
            if ok:
                try:
                    with open(tmp_pdf, "rb") as f:
                        default_storage.save(pdf_rel, ContentFile(f.read()))
                    if self.arquivo_pdf.name != pdf_rel:
                        self.arquivo_pdf.name = pdf_rel
                        super().save(update_fields=["arquivo_pdf"])
                except Exception as e:
                    print("⚠️ Falha ao salvar PDF no storage:", e)

    def __str__(self):
        return self.titulo or "(sem título)"


class Autor(models.Model):
    nome = models.CharField(max_length=100)
    visivel = models.BooleanField(default=True)
    def __str__(self): return self.nome

class Area(models.Model):
    nome = models.CharField(max_length=100)
    visivel = models.BooleanField(default=True)
    def __str__(self): return self.nome

def caminho_imagem(instance, filename):
    return f"imagens/artigos/temp_{filename}"

def caminho_arquivo(instance, filename):
    return f"uploads/artigo_{instance.slug or 'temp'}_{filename}"
