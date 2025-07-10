import os
import sys
import django

# ==== Configuração do Django ====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'pralbinomarks'))  # ajuste para seu projeto

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pralbinomarks.settings')
django.setup()

# ==== Importações do projeto ====
from A_Lei_no_NT.models import Artigo
from A_Lei_no_NT.utils import docx_para_html, gerar_slug, renomear_com_slug
from django.utils import timezone
from django.core.files import File

# ==== Caminhos ====
CAMINHO_DOCX = r'C:\Users\Wanderley\Apps\ExtratorAlbino\downloads\Publicar\a-justica-de-deus-e-a-justica-dos-fariseus.docx'
CAMINHO_IMAGEM = r'C:\Users\Wanderley\Apps\Pr_Albino_Marks_restaurado\media\imagens\artigos\a-justica-de-deus-e-a-justica-dos-fariseus.png'

# ==== Etapas ====
print("📄 Lendo documento Word...")
html, titulo = docx_para_html(CAMINHO_DOCX)
slug = gerar_slug(titulo)

print("📝 Criando artigo...")
artigo = Artigo(
    titulo=titulo,
    slug=slug,
    conteudo_html=html,
    publicado_em=timezone.now(),
    visivel=True
)
artigo.save()

# ==== Associar imagem de capa ====
print("🖼️ Adicionando imagem de capa...")
if os.path.exists(CAMINHO_IMAGEM):
    with open(CAMINHO_IMAGEM, 'rb') as f:
        nome_final = renomear_com_slug(CAMINHO_IMAGEM, slug)
        artigo.imagem_capa.save(nome_final, File(f), save=True)
        print(f"✅ Imagem salva como: {nome_final}")
else:
    print("⚠️ Imagem não encontrada:", CAMINHO_IMAGEM)

# ==== Associar cópia do arquivo .docx ====
print("📎 Salvando cópia do Word...")
if os.path.exists(CAMINHO_DOCX):
    with open(CAMINHO_DOCX, 'rb') as f:
        nome_final = renomear_com_slug(CAMINHO_DOCX, slug)
        artigo.arquivo_word.save(nome_final, File(f), save=True)
        print(f"✅ Arquivo Word salvo como: {nome_final}")
else:
    print("⚠️ Arquivo Word não encontrado:", CAMINHO_DOCX)

print("🎉 Artigo importado com sucesso:", artigo.titulo)