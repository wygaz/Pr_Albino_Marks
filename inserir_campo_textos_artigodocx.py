import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pralbinomarks.settings')
django.setup()

from A_Lei_no_NT.models import Artigo, Autor, Area

def atualizar_caminho_arquivo(titulo, autor_nome, area_nome, caminho_arquivo_docx):
    autor, created = Autor.objects.get_or_create(nome_autor=autor_nome)
    area, created = Area.objects.get_or_create(nome_area=area_nome)
    artigo, created = Artigo.objects.get_or_create(
        titulo=titulo,
        defaults={'caminho_arquivo_docx': caminho_arquivo_docx.replace('\\', '/'), 'autor': autor, 'area': area},
    )

    if not created:
        artigo.caminho_arquivo_docx = caminho_arquivo_docx.replace('\\', '/')
        artigo.autor = autor
        artigo.area = area
        artigo.save()

# Exemplo de uso para seis instâncias
atualizar_caminho_arquivo(
    titulo='OS ESCRITORES DO NT E A LEI',
    autor_nome='Pr. Albino Marks',
    area_nome='Teologia',
    caminho_arquivo_docx=r'C:/Users/Wanderley/Apps/Albino_Marks/A_Lei_no_NT/Templates/A_Lei_no_NT/Textos/DOCX/1_OS_ESCRITORES_DO_NT_E_A_lei.docx'
)

atualizar_caminho_arquivo(
    titulo='O APÓSTOLO PAULO E A LEI',
    autor_nome='Pr. Albino Marks',
    area_nome='Teologia',
    caminho_arquivo_docx=r'C:/Users/Wanderley/Apps/Albino_Marks/A_Lei_no_NT/Templates/A_Lei_no_NT/Textos/DOCX/2_O_APOSTOLO_PAULO_E_A_LEI.docx'
)

atualizar_caminho_arquivo(
    titulo='O NOVO TESTAMENTO, JESUS E A LEI',
    autor_nome='Pr. Albino Marks',
    area_nome='Teologia',
    caminho_arquivo_docx=r'C:/Users/Wanderley/Apps/Albino_Marks/A_Lei_no_NT/Templates/A_Lei_no_NT/Textos/DOCX/3_O_NT_JESUS_E_A_LEI.docx'
)

atualizar_caminho_arquivo(
    titulo='JESUS E A LEI (NÓMOS)',
    autor_nome='Pr. Albino Marks',
    area_nome='Teologia',
    caminho_arquivo_docx=r'C:/Users/Wanderley/Apps/Albino_Marks/A_Lei_no_NT/Templates/A_Lei_no_NT/Textos/DOCX/4_JESUS_E_A_LEI-NOMOS.docx'
)

atualizar_caminho_arquivo(
    titulo='JESUS, NÃO REVOGANDO, MAS MAGNIFICANDO A LEI',
    autor_nome='Pr. Albino Marks',
    area_nome='Teologia',
    caminho_arquivo_docx=r'C:/Users/Wanderley/Apps/Albino_Marks/A_Lei_no_NT/Templates/A_Lei_no_NT/Textos/DOCX/5_JESUS_NAO_REVOGANDO_MAS_MAGNIFICANDO_A_LEI.docx'
)

atualizar_caminho_arquivo(
    titulo='A JUSTIÇA DE DEUS E A JUSTIÇA DOS FARISEUS',
    autor_nome='Pr. Albino Marks',
    area_nome='Teologia',
    caminho_arquivo_docx=r'C:/Users/Wanderley/Apps/Albino_Marks/A_Lei_no_NT/Templates/A_Lei_no_NT/Textos/DOCX/6_A_JUSTICA_DE_DEUS_E_A_JUSTICA_DOS_FARISEUS.docx'
)
