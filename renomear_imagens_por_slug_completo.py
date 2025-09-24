# renomear_imagens_por_slug_completo.py  (S3-safe)
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
from django.core.files.storage import default_storage
from django.conf import settings
from A_Lei_no_NT.models import Artigo
from A_Lei_no_NT.utils_storage import open_file

print("🔍 Iniciando varredura de imagens com base no slug dos artigos...")

artigos = Artigo.objects.exclude(slug__isnull=True)

for artigo in artigos:
    if not artigo.imagem_capa:
        print(f"❌ Artigo '{artigo.titulo}' não possui imagem associada.")
        continue

    old_name = artigo.imagem_capa.name  # ex: 'imagens/artigos/foo.jpg'
    if not old_name:
        print(f"⚠️ Nome de imagem vazio para '{artigo.titulo}'.")
        continue

    ext = os.path.splitext(old_name)[1]
    nome_esperado = f"{artigo.slug}{ext}"
    novo_name = f"imagens/artigos/{nome_esperado}"

    if os.path.basename(old_name) == nome_esperado:
        print(f"✅ Imagem correta: {nome_esperado}")
        continue

    # Conflito?
    if default_storage.exists(novo_name):
        resposta = input(f"⚠️ Já existe '{novo_name}'. Substituir? [1] Sim  [2] Não ➤ ")
        if resposta.strip() != "1":
            print("⏭️ Pulado pelo usuário.")
            continue
        default_storage.delete(novo_name)

    # Copia no storage e apaga o antigo
    try:
        with open_file(old_name, "rb") as src:
            default_storage.save(novo_name, src)
        if default_storage.exists(old_name):
            default_storage.delete(old_name)

        artigo.imagem_capa.name = novo_name
        artigo.save(update_fields=["imagem_capa"])
        print(f"🔁 Renomeado: {os.path.basename(old_name)} → {nome_esperado}")
    except Exception as e:
        print(f"❌ Erro ao renomear imagem para '{artigo.titulo}': {e}")

print("🏁 Renomeação finalizada.")
