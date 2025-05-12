import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pralbinomarks.settings')
django.setup()

from A_Lei_no_NT.models import Artigo, Autor, Area, Midia

# Criando áreas
teologia = Area.objects.create(nome_area="Teologia")
historia = Area.objects.create(nome_area="História")

# Criando autores com os novos campos 'biografia', 'midia' e 'foto'
autor1 = Autor.objects.create(
    nome_autor="Autor 1", 
    biografia="Biografia do Autor 1", 
    midia="A_Lei_no_NT/Imagens/Autores/autor1_video.mp4", 
    foto="A_Lei_no_NT/Imagens/Autores/autor1.jpg"
)
autor2 = Autor.objects.create(
    nome_autor="Autor 2", 
    biografia="Biografia do Autor 2", 
    midia="A_Lei_no_NT/Imagens/Autores/autor2_podcast.mp3", 
    foto="A_Lei_no_NT/Imagens/Autores/autor2.jpg"
)

# Criando mídias
midia1 = Midia.objects.create(tipo="Imagem", caminho="A_Lei_no_NT/Imagens/1.png", descricao="Imagem 1")
midia2 = Midia.objects.create(tipo="Imagem", caminho="A_Lei_no_NT/Imagens/2.png", descricao="Imagem 2")

# Criando artigos
Artigo.objects.create(titulo="Artigo 1", texto="Texto do artigo 1", area=teologia, autor=autor1, midia=midia1)
Artigo.objects.create(titulo="Artigo 2", texto="Texto do artigo 2", area=historia, autor=autor2, midia=midia2)
Artigo.objects.create(titulo="Artigo 3", texto="Texto do artigo 3", area=teologia, autor=autor1, midia=None)

print("Dados de exemplo inseridos com sucesso!")
