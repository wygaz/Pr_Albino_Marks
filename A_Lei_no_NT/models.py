import os
from django.utils import timezone
from django.db.models import Max
from django.db import models
from django.core.files.storage import default_storage

from A_Lei_no_NT.utils import docx_para_html, gerar_slug
from A_Lei_no_NT.utils_storage import open_file


def caminho_pdf(instance, filename):
    # Mantemos apenas a pasta; o nome final é decidido no upload
    return f"pdfs/artigos/{filename}"


class Artigo(models.Model):
    titulo = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, blank=True)  # permite gerar no save()
    conteudo_html = models.TextField(null=True, blank=True)
    imagem_capa = models.ImageField(upload_to="imagens/artigos/", null=True, blank=True)
    arquivo_word = models.FileField(upload_to="uploads/artigos/", null=True, blank=True)
    arquivo_pdf = models.FileField(upload_to=caminho_pdf, null=True, blank=True)
    publicado_em = models.DateTimeField(null=True, blank=True)
    ordem = models.IntegerField(null=True, blank=True)
    visivel = models.BooleanField(default=True)
    autor = models.ForeignKey("Autor", on_delete=models.SET_NULL, null=True, blank=True)
    area = models.ForeignKey("Area", on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # 1) Extrair HTML/título/autor do DOCX, se aplicável (blindado)
        if self.arquivo_word and not self.conteudo_html:
            try:
                html, titulo_extraido, autor_detectado = docx_para_html(self.arquivo_word)
                self.conteudo_html = html
                if not self.titulo:
                    self.titulo = (titulo_extraido or "").strip()
                if autor_detectado:
                    autor_obj, _ = Autor.objects.get_or_create(nome=autor_detectado)
                    self.autor = autor_obj
            except Exception as e:
                print(f"⚠️ Erro ao extrair HTML do DOCX: {e}")

        # 2) Slug único (gera só se estiver vazio)
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
            maior = Artigo.objects.aggregate(Max("ordem"))["ordem__max"] or 0
            self.ordem = maior + 1

        super().save(*args, **kwargs)  # garante PK

        # 4) Renomear imagem de capa pelo slug (S3-safe)
        if self.imagem_capa and self.slug:
            old_name = self.imagem_capa.name
            ext = os.path.splitext(old_name)[1]
            novo_rel = f"imagens/artigos/{self.slug}{ext}"
            if old_name != novo_rel:
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


# Helpers não usados pelos campos; se não usar em outro lugar, pode remover
def caminho_imagem(instance, filename):
    return f"imagens/artigos/temp_{filename}"


def caminho_arquivo(instance, filename):
    return f"uploads/artigo_{instance.slug or 'temp'}_{filename}"
