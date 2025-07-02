from django.db import models
from django.utils.text import slugify
from django.db.models import Max
from django.utils import timezone
from A_Lei_no_NT.utils import docx_para_html, gerar_slug


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
    return f"capas/artigo_{instance.pk}_{filename}"


def caminho_arquivo(instance, filename):
    return f"uploads/artigo_{instance.pk}_{filename}"


class Artigo(models.Model):
    titulo = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    conteudo_html = models.TextField(null=True, blank=True)
    imagem_capa = models.ImageField(upload_to=caminho_imagem, null=True, blank=True)
    arquivo_word = models.FileField(upload_to=caminho_arquivo, null=True, blank=True)
    publicado_em = models.DateTimeField(null=True, blank=True)
    ordem = models.IntegerField(null=True, blank=True)
    visivel = models.BooleanField(default=True)

    autor = models.ForeignKey(Autor, on_delete=models.SET_NULL, null=True, blank=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Gerar HTML e título a partir do Word
        if self.arquivo_word and not self.conteudo_html:
            html, titulo_extraido = docx_para_html(self.arquivo_word)
            self.conteudo_html = html
            if not self.titulo:
                self.titulo = titulo_extraido.strip()

        # Gerar slug único
        if not self.slug and self.titulo:
            slug_base = gerar_slug(self.titulo)
            slug = slug_base
            contador = 1
            while Artigo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{slug_base}-{contador}"
                contador += 1
            self.slug = slug

        # Data de publicação automática
        if not self.publicado_em:
            self.publicado_em = timezone.now()

        # Ordem automática
        if self.ordem is None:
            maior_ordem = Artigo.objects.aggregate(Max('ordem'))['ordem__max'] or 0
            self.ordem = maior_ordem + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo or "(sem título)"
