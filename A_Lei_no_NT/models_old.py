from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.db.models import Max
from A_Lei_no_NT.utils import gerar_slug, docx_para_html


class Autor(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Area(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Midia(models.Model):
    titulo = models.CharField(max_length=100)
    arquivo = models.FileField(upload_to='media/')

    def __str__(self):
        return self.titulo


class Artigo(models.Model):
    titulo = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    conteudo_html = models.TextField(blank=True, null=True)
    ordem = models.PositiveIntegerField(blank=True, null=True)
    imagem_capa = models.ImageField(upload_to='imagens/artigos/', blank=True, null=True)
    arquivo_word = models.FileField(
        upload_to='artigos/word/',
        validators=[FileExtensionValidator(allowed_extensions=['docx'])],
        blank=True,
        null=True
    )
    visivel = models.BooleanField("Visível ao público", default=True)
    publicado_em = models.DateTimeField(default=timezone.now)
    data_publicacao = models.DateField(null=True, blank=True)
    midia = models.FileField(upload_to='midia/artigos/', null=True, blank=True)
    area = models.ForeignKey('Area', on_delete=models.SET_NULL, null=True, blank=True)
    autor = models.ForeignKey('Autor', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Extrair conteúdo do Word, se disponível
        if self.arquivo_word and not self.conteudo_html:
            html, titulo_extraido = docx_para_html(self.arquivo_word)
            self.conteudo_html = html
            if not self.titulo:
                self.titulo = titulo_extraido.strip()

        # Gerar slug a partir do título
        if not self.slug and self.titulo:
            slug_base = gerar_slug(self.titulo)
            slug = slug_base
            contador = 1
            while Artigo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{slug_base}-{contador}"
                contador += 1
            self.slug = slug

        # Definir ordem automaticamente
        if self.ordem is None:
            maior_ordem = Artigo.objects.aggregate(Max('ordem'))['ordem__max'] or 0
            self.ordem = maior_ordem + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo or "(sem título)"
