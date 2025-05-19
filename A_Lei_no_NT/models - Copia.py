from django.db import models
from django.utils.text import slugify

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
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)  # Novo campo
    conteudo_html = models.TextField()
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    midia = models.ForeignKey(Midia, on_delete=models.SET_NULL, null=True, blank=True)
    imagem = models.ImageField(upload_to='artigos/', null=True, blank=True)
    data_publicacao = models.DateField(null=True, blank=True)
    ordem = models.IntegerField()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo