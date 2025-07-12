import sys
import os
import django
import datetime
from django.utils import timezone

# Caminho absoluto para a raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)


# Configuração do Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pralbinomarks.settings")
django.setup()

from A_Lei_no_NT.models import Artigo
from A_Lei_no_NT.utils import gerar_slug, docx_para_html

# Caminhos fixos (ajuste conforme necessário)
caminho_docx = r"C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\media\imagens\Publicar"
caminho_imagens = r"C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\media\imagens\artigo"

# Lista e ordena os arquivos .docx pela numeração inicial
arquivos = sorted([f for f in os.listdir(caminho_docx) if f.endswith('.docx')])

for arquivo in arquivos:
    caminho_arquivo = os.path.join(caminho_docx, arquivo)
    print(f"\n📄 Processando: {arquivo}")
    
    try:
        # Converte o conteúdo do docx em HTML e extrai o título
        html, titulo = docx_para_html(caminho_arquivo)
        slug = gerar_slug(titulo)

        # Cria o novo artigo
        obj = Artigo(
            titulo=titulo,
            slug=slug,
            conteudo_html=html,
            visivel=True,
            publicado_em=datetime.now()
        )

        # Procura a imagem correspondente
        for ext in ['.jpg', '.png']:
            caminho_img = os.path.join(caminho_imagens, f"{slug}{ext}")
            if os.path.exists(caminho_img):
                obj.imagem_capa.name = f"imagens/artigos/{slug}{ext}"
                break

        obj.save()
        print(f"✅ Publicado: {titulo}")

    except Exception as e:
        print(f"❌ Erro ao processar {arquivo}: {e}")
