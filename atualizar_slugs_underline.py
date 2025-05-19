import os
import sys
import django
from pathlib import Path
from django.utils.text import slugify

# Caminho do projeto
PROJETO_ROOT = Path("C:/Users/Wanderley/Apps/Pr_Albino_Marks_restaurado")
sys.path.append(str(PROJETO_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pralbinomarks.settings")

# Carregar variáveis de ambiente
import environ
env = environ.Env()
environ.Env.read_env(PROJETO_ROOT / ".env")

# Inicializar Django
django.setup()

from A_Lei_no_NT.models import Artigo

# Atualizar todos os slugs com underline
total = 0
for artigo in Artigo.objects.all():
    novo_slug = slugify(artigo.titulo).replace('-', '_')
    if artigo.slug != novo_slug:
        artigo.slug = novo_slug
        artigo.save()
        print(f"✅ Atualizado: {artigo.titulo} → {artigo.slug}")
        total += 1

print(f"🎯 Total de artigos atualizados: {total}")
