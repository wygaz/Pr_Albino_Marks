# models.py
import os
import re
from unidecode import unidecode
from django.db import models

class Artigo(models.Model):
    titulo = models.CharField(max_length=200)
    conteudo_html = models.TextField()  # Campo único para armazenar o conteúdo HTML
    autor = models.ForeignKey('Autor', on_delete=models.CASCADE)
    area = models.ForeignKey('Area', on_delete=models.CASCADE)
    midia = models.ImageField(upload_to='imagens/', blank=True, null=True)
    data_publicacao = models.DateField(default='2000-01-01')
    ordem = models.IntegerField()

    def __str__(self):
        return self.titulo

    @property
    def nome_arquivo(self):
        return self.get_file_name_from_title(self.titulo)

    def get_html_path(self):
        return os.path.join('media', 'htmls', self.nome_arquivo)

    @staticmethod
    def get_file_name_from_title(title):
        title_unaccented = unidecode(title)
        title_cleaned = re.sub(r'[^a-zA-Z0-9_]+', '', title_unaccented.replace(" ", "_"))
        return title_cleaned.upper() + '.html'
    
class Autor(models.Model):
    nome_autor = models.CharField(max_length=200)
    biografia = models.TextField()
    midia = models.FileField(upload_to='A_Lei_no_NT/Imagens/Autores/', null=True, blank=True)
    foto = models.ImageField(upload_to='A_Lei_no_NT/Imagens/Autores/', null=True, blank=True)

    def __str__(self):
        return self.nome_autor

class Area(models.Model):
    nome_area = models.CharField(max_length=200)
    descricao = models.TextField(default='Descrição padrão temporária')  # Adicione um valor padrão
    
    def __str__(self):
        return self.nome_area

class Midia(models.Model):
    nome_midia = models.CharField(max_length=200, default='Nome Padrão Temporário')  # Valor padrão temporário
    tipo = models.CharField(max_length=50)
    arquivo = models.CharField(max_length=200)
    descricao = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.nome_midia
