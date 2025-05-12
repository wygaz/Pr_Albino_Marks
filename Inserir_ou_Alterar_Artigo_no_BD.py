import os
import django
from django.conf import settings

# Configure o caminho do módulo de configurações do seu projeto Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pralbinomarks.settings')

# Configure o Django
django.setup()

\l Blog.models import Artigo, Autor, Area

def inserir_ou_atualizar_artigo(titulo, autor_nome, area_nome, caminho_arquivo_html):
    # Lê o conteúdo do arquivo HTML
    with open(caminho_arquivo_html, 'r', encoding='utf-8') as file:
        conteudo_html = file.read()

    # Verifica se o autor e a área existem, caso contrário, cria-os
    autor, created = Autor.objects.get_or_create(nome_autor=autor_nome)
    area, created = Area.objects.get_or_create(nome_area=area_nome)

    # Verifica se o artigo já existe no banco de dados
    artigo, created = Artigo.objects.get_or_create(
        titulo=titulo,
        defaults={'texto': conteudo_html, 'autor': autor, 'area': area}
    )

    if not created:
        # Se o artigo já existe, atualiza os campos
        artigo.texto = conteudo_html
        artigo.autor = autor
        artigo.area = area
        artigo.save()
        print(f"Artigo '{titulo}' atualizado no banco de dados.")
    else:
        print(f"Artigo '{titulo}' inserido no banco de dados.")

# Exemplo de uso
caminho_arquivo_html = r'C:\Users\Wanderley\Apps\Albino_Marks\A_Lei_no_NT\Templates\A_Lei_no_NT\Textos\1_OS_ESCRITORES_DO_NT_E_A_lei.html'
inserir_ou_atualizar_artigo(
    titulo='OS ESCRITORES DO NT E A LEI',
    autor_nome='Pr. Albino Marks',
    area_nome='Teologia',
    caminho_arquivo_html=caminho_arquivo_html
)
