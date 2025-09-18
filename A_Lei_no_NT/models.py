import os
import subprocess
import sys
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Max
from django.db import models
from django.core.files import File
from django.conf import settings

from A_Lei_no_NT.utils import docx_para_html, gerar_slug

# ... (Autor, Area, caminho_imagem, caminho_arquivo iguais)

def caminho_pdf(instance, filename):
    # mantemos apenas a pasta; o nome final será pelo slug
    return f"pdfs/artigos/{filename}"

class Artigo(models.Model):
    titulo = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    conteudo_html = models.TextField(null=True, blank=True)
    imagem_capa = models.ImageField(upload_to="imagens/artigos/", null=True, blank=True)
    arquivo_word = models.FileField(upload_to="uploads/artigos/", null=True, blank=True)
    arquivo_pdf = models.FileField(upload_to=caminho_pdf, null=True, blank=True)  # <-- novo
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
            from django.db.models import Max
            maior = Artigo.objects.aggregate(Max('ordem'))['ordem__max'] or 0
            self.ordem = maior + 1

        super().save(*args, **kwargs)  # salva para garantir PK

        # 4) Renomear imagem de capa pelo slug (igual você já fazia)
        if self.imagem_capa:
            antiga_path = self.imagem_capa.path
            ext = os.path.splitext(antiga_path)[1]
            novo_nome = f"{self.slug}{ext}"
            novo_rel = f"imagens/artigos/{novo_nome}"
            novo_abs = os.path.join(settings.MEDIA_ROOT, "imagens", "artigos", novo_nome)
            if not antiga_path.endswith(novo_nome):
                try:
                    os.makedirs(os.path.dirname(novo_abs), exist_ok=True)
                    os.replace(antiga_path, novo_abs)
                    self.imagem_capa.name = novo_rel
                    super().save(update_fields=["imagem_capa"])
                except Exception as e:
                    print(f"⚠️ Erro ao renomear imagem de capa: {e}")

        # 5) Gerar/atualizar PDF a partir do DOCX se necessário
        if self.arquivo_word:
            self._ensure_pdf_from_docx()

            

    def _ensure_pdf_from_docx(self):
        """
        Gera (ou regenera) o PDF baseado no arquivo_word.
        • Linux: tenta LibreOffice headless
        • Windows/macOS: tenta docx2pdf (se instalado)
        """
        try:
            docx_path = self.arquivo_word.path
        except Exception:
            return

        # destino final
        pdf_filename = f"{self.slug}.pdf" if self.slug else "temp.pdf"
        pdf_rel = os.path.join("pdfs", "artigos", pdf_filename)
        pdf_abs = os.path.join(settings.MEDIA_ROOT, "pdfs", "artigos", pdf_filename)

        # se PDF já existe e é mais novo que o DOCX, não refaz
        if os.path.exists(pdf_abs):
            if os.path.getmtime(pdf_abs) >= os.path.getmtime(docx_path):
                if not self.arquivo_pdf:
                    self.arquivo_pdf.name = pdf_rel
                    super().save(update_fields=["arquivo_pdf"])
                return

        os.makedirs(os.path.dirname(pdf_abs), exist_ok=True)

        ok = False
        # 1) Linux / LibreOffice
        if sys.platform.startswith("linux"):
            try:
                # Converte para a pasta destino; LibreOffice sempre cria com o mesmo nome base
                subprocess.run(
                    ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir",
                     os.path.dirname(pdf_abs), docx_path],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                ok = os.path.exists(pdf_abs)
            except Exception as e:
                print("⚠️ LibreOffice não funcionou:", e)

        # 2) Fallback: docx2pdf (Windows/macOS)
        if not ok:
            try:
                from docx2pdf import convert as docx2pdf_convert
                docx2pdf_convert(docx_path, pdf_abs)
                ok = os.path.exists(pdf_abs)
            except Exception as e:
                print("⚠️ docx2pdf indisponível:", e)

        if ok:
            # aponta o FileField para o arquivo gerado
            rel = pdf_rel.replace("\\", "/")
            if self.arquivo_pdf.name != rel:
                self.arquivo_pdf.name = rel
                super().save(update_fields=["arquivo_pdf"])

    def __str__(self):
        return self.titulo or "(sem título)"



class Autor(models.Model):
    nome = models.CharField(max_length=100)
    visivel = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Area(models.Model):
    nome = models.CharField(max_length=100)
    visivel = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


def caminho_imagem(instance, filename):
    # Temporário – será renomeado após o slug estar disponível
    return f"imagens/artigos/temp_{filename}"


def caminho_arquivo(instance, filename):
    # Grava diretamente com base no slug (o .docx define o slug ao ser salvo)
    return f"uploads/artigo_{instance.slug or 'temp'}_{filename}"


