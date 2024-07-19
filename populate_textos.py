import os
import django

# Configurar o Django para usar as configurações do projeto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Albino_Marks.settings')
django.setup()

from A_Lei_no_NT.models import Texto

# Dados dos textos
textos = [
    {
        'title': 'Os Escritores do Novo Testamento e a Lei',
        'filename': '1_OS_ESCRITORES_DO_NT_E_A_LEI.html',
        'image': 'A_Lei_no_NT/Imagens/1_OS_ESCRITORES_DO_NT_E_A_lei.jpg'
    },
    {
        'title': 'O Apóstolo Paulo e a Lei',
        'filename': '2_O_APOSTOLO_PAULO_E_A_LEI.html',
        'image': 'A_Lei_no_NT/Imagens/2_O_APOSTOLO_PAULO_E_A_LEI.jpg'
    },
    {
        'title': 'O NT, Jesus e a Lei',
        'filename': '3_O_NT_JESUS_E_A_LEI.html',
        'image': 'A_Lei_no_NT/Imagens/3_O_NT_JESUS_E_A_LEI.jpg'
    },
    {
        'title': 'Jesus e a Lei (Nomos)',
        'filename': '4_JESUS_E_A_LEI-NOMOS.html',
        'image': 'A_Lei_no_NT/Imagens/4_JESUS_E_A_LEI-NOMOS.jpg'
    },
    {
        'title': 'Jesus Não Revogou, Mas Magnificou a Lei',
        'filename': '5_JESUS_NAO_REVOGOU_MAS_MAGNIFICOU_A_LEI.html',
        'image': 'A_Lei_no_NT/Imagens/5_JESUS_NAO_REVOGOU_MAS_MAGNIFICOU_A_LEI.jpg'
    },
    {
        'title': 'A Justiça de Deus e a dos Fariseus',
        'filename': '6_A_JUSTICA_DE_DEUS_E_A_DOS_FARISEUS.html',
        'image': 'A_Lei_no_NT/Imagens/6_A_JUSTICA_DE_DEUS_E_A_DOS_FARISEUS.jpg'
    },
]

# Inserir os dados no banco de dados
for texto_data in textos:
    Texto.objects.create(**texto_data)

print('Dados inseridos com sucesso!')
