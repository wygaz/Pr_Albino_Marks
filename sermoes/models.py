# sermoes/models.py
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Sermao(models.Model):
    titulo = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    serie = models.CharField(max_length=255, blank=True)
    resumo = models.TextField(blank=True)
    conteudo_html = models.TextField(blank=True)

    pdf_tablet = models.FileField(upload_to='pdfs/sermoes/tablet/', blank=True, null=True)
    pdf_a4 = models.FileField(upload_to='pdfs/sermoes/a4/', blank=True, null=True)
    pdf_a5 = models.FileField(upload_to='pdfs/sermoes/a5/', blank=True, null=True)
    relatorio_tecnico_pdf = models.FileField(upload_to='pdfs/relatorios_tecnicos/', blank=True, null=True)
    docx_a4 = models.FileField(upload_to='docs/sermoes/', blank=True, null=True)
    imagem_capa = models.ImageField(upload_to='imagens/sermoes/', blank=True, null=True)

    visivel = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
    data_publicacao = models.DateField(default=timezone.now)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordem', 'titulo']
        verbose_name = 'Sermão'
        verbose_name_plural = 'Sermões'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
