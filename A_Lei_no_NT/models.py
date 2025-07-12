import os
from django.template.loader import render_to_string
from weasyprint import HTML
from django.utils import timezone
from django.db.models import Max

from django.db import models
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
    # Temporário – será renomeado após o slug estar disponível
    return f"imagens/artigos/temp_{filename}"


def caminho_arquivo(instance, filename):
    # Grava diretamente com base no slug (o .docx define o slug ao ser salvo)
    return f"uploads/artigo_{instance.slug or 'temp'}_{filename}"


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
        # Gerar HTML, título e autor a partir do Word
        if self.arquivo_word and not self.conteudo_html:
            html, titulo_extraido, autor_detectado = docx_para_html(self.arquivo_word)
            self.conteudo_html = html
            if not self.titulo:
                self.titulo = titulo_extraido.strip()
            if autor_detectado:
                from .models import Autor
                autor_obj, _ = Autor.objects.get_or_create(nome=autor_detectado)
                self.autor = autor_obj

        # Gerar slug único
        if not self.slug and self.titulo:
            slug_base = gerar_slug(self.titulo)
            slug = slug_base
            contador = 1
            while Artigo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{slug_base}-{contador}"
                contador += 1
            self.slug = slug

        # Definir data de publicação se não estiver definida
        if not self.publicado_em:
            self.publicado_em = timezone.now()

        # Definir ordem automática se não houver
        if self.ordem is None:
            maior_ordem = Artigo.objects.aggregate(Max('ordem'))['ordem__max'] or 0
            self.ordem = maior_ordem + 1

        # Primeiro salvamento (para garantir que o objeto tenha PK)
        super().save(*args, **kwargs)

        # Renomear a imagem de capa com base no slug
        if self.imagem_capa:
            antiga_path = self.imagem_capa.path
            ext = os.path.splitext(antiga_path)[1]
            novo_nome = f"{self.slug}{ext}"
            novo_path = os.path.join("media/imagens/artigos", novo_nome)

            if not antiga_path.endswith(novo_nome):
                try:
                    os.rename(antiga_path, novo_path)
                    self.imagem_capa.name = f"imagens/artigos/{novo_nome}"
                    super().save(update_fields=["imagem_capa"])
                except Exception as e:
                    print(f"⚠️ Erro ao renomear imagem de capa: {e}")

    def __str__(self):
        return self.titulo or "(sem título)"
