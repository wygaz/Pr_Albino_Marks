# === CONFIGURAÇÃO DO DJANGO ===
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'pralbinomarks'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pralbinomarks.settings')
django.setup()

# === IMPORTAÇÕES ===
from django.core.files import File
from django.conf import settings
from A_Lei_no_NT.models import Artigo

# === CAMINHO DAS IMAGENS ===
CAMINHO_IMAGENS = os.path.join(settings.MEDIA_ROOT, "imagens", "artigos")

print("🔍 Iniciando varredura de imagens com base no slug dos artigos...")

artigos = Artigo.objects.exclude(slug__isnull=True)

for artigo in artigos:
    if not artigo.imagem_capa:
        print(f"❌ Artigo '{artigo.titulo}' não possui imagem associada.")
        continue

    try:
        caminho_atual = artigo.imagem_capa.path
    except Exception as e:
        print(f"⚠️ Caminho de imagem inválido para '{artigo.titulo}': {e}")
        continue

    ext = os.path.splitext(caminho_atual)[1]
    nome_esperado = f"{artigo.slug}{ext}"
    caminho_destino = os.path.join(CAMINHO_IMAGENS, nome_esperado)

    if os.path.basename(caminho_atual) == nome_esperado:
        print(f"✅ Imagem correta: {nome_esperado}")
        continue

    # Verifica conflito de nome
    if os.path.exists(caminho_destino):
        print(f"⚠️ Já existe uma imagem com o nome: {nome_esperado}")
        resposta = input("Deseja substituir a imagem existente? [1] Sim  [2] Não ➤ ")
        if resposta.strip() != "1":
            print("⏭️ Pulado pelo usuário.")
            continue
        os.remove(caminho_destino)

    # Tenta renomear fisicamente
    try:
        os.rename(caminho_atual, caminho_destino)
        artigo.imagem_capa.name = f"imagens/artigos/{nome_esperado}"
        artigo.save()
        print(f"🔁 Renomeado: {os.path.basename(caminho_atual)} → {nome_esperado}")
    except Exception as e:
        print(f"❌ Erro ao renomear imagem para '{artigo.titulo}': {e}")

print("🏁 Renomeação finalizada.")