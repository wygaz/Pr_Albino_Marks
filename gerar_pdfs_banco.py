import os
import django
from django.conf import settings
from django.template.loader import render_to_string

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pralbinomarks.settings')
django.setup()

from A_Lei_no_NT.models import Artigo  # ajuste se necessário

# Caminho de saída
PDF_DIR = os.path.join(settings.MEDIA_ROOT, 'pdfs')
os.makedirs(PDF_DIR, exist_ok=True)

# Iterar pelos artigos
for artigo in Artigo.objects.all():
    html_renderizado = render_to_string('A_Lei_no_NT/modelo_artigo_pdf.html', {
        'titulo': artigo.titulo,
        'conteudo': artigo.conteudo_html
    })

    caminho_saida = os.path.join(PDF_DIR, f'{artigo.slug}.pdf')
    HTML(string=html_renderizado).write_pdf(caminho_saida)
    print(f"✅ PDF gerado: {caminho_saida}")
