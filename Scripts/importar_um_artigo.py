import os
from django.utils import timezone
from django.core.files.images import ImageFile
from core.models import Artigo  # ajuste o nome do app se necessário
from utils import docx_para_html, gerar_slug  # certifique-se de que está importando corretamente

# === CONFIGURAÇÕES ===
NOME_ARQUIVO = 'a-justica-de-deus-e-a-justica-dos-fariseus'
CAMINHO_DOCX = fr'C:\Users\Wanderley\Apps\ExtratorAlbino\downloads\Publicar\{NOME_ARQUIVO}.docx'
CAMINHO_IMG = fr'C:\Users\Wanderley\Apps\ExtratorAlbino\media\imagens\artigos\{NOME_ARQUIVO}.jpg'

# === CONVERSÃO DO .DOCX PARA HTML E EXTRAÇÃO DO TÍTULO ===
html, titulo_extraido = docx_para_html(CAMINHO_DOCX)
slug = gerar_slug(titulo_extraido)

print(f"\n🔍 Título detectado: {titulo_extraido}")
print(f"🔗 Slug gerado: {slug}")

# === CRIAÇÃO DO OBJETO NO BD ===
artigo = Artigo(
    titulo=titulo_extraido,
    slug=slug,
    conteudo_html=html,
    autor="Pr. Albino Marks",
    visivel=True,
    publicado_em=timezone.now()
)

# === ASSOCIAÇÃO DA IMAGEM DE CAPA ===
if os.path.exists(CAMINHO_IMG):
    with open(CAMINHO_IMG, 'rb') as img_file:
        artigo.imagem_capa.save(f'{slug}.jpg', ImageFile(img_file), save=False)
        print("🖼️ Imagem de capa associada com sucesso.")
else:
    print("⚠️ Imagem de capa NÃO encontrada. Continuando sem imagem...")

# === SALVAMENTO ===
artigo.save()
print("✅ Artigo importado com sucesso!")
