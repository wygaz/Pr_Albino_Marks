import os
# Adiciona o caminho raiz do projeto ao sys.path
import sys
# Adiciona o caminho raiz do projeto ao sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
import django
from datetime import datetime


# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pralbinomarks.settings')
django.setup()

# Agora você pode importar normalmente
from A_Lei_no_NT.utils import docx_para_html
from A_Lei_no_NT.models import Artigo

# Caminho da pasta com artigos prontos para publicar
CAMINHO_PUBLICAR = r'C:\Users\Wanderley\Apps\ExtratorAlbino\downloads\Publicar'


AUTOR_PADRAO = 'Pr. Albino Marks'

def importar_artigos():
    arquivos = [f for f in os.listdir(CAMINHO_PUBLICAR) if f.endswith('.docx')]

    for nome_arquivo in arquivos:
        caminho = os.path.join(CAMINHO_PUBLICAR, nome_arquivo)
        print(f"\n📥 Processando: {nome_arquivo}")

        try:
            html, titulo = docx_para_html(caminho)
            slug = titulo.lower().strip().replace(' ', '-').replace('.', '').replace(',', '')

            print(f"Título: {titulo}")
            print(f"Slug: {slug}")

            if Artigo.objects.filter(slug=slug).exists():
                print(f"⚠️ Já existe artigo com slug '{slug}'. Ignorando.")
                continue

            artigo = Artigo(
                titulo=titulo,
                slug=slug,
                conteudo_html=html,
                autor=AUTOR_PADRAO,
                visivel=True,
                ordem=Artigo.objects.count() + 1,
                publicado_em=datetime.now()
            )
            artigo.save()
            print(f"✅ Artigo '{titulo}' importado com sucesso.")

        except Exception as e:
            print(f"❌ Erro ao importar '{nome_arquivo}': {e}")

if __name__ == '__main__':
    importar_artigos()