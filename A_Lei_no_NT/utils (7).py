
import os
import re
import uuid
from bs4 import BeautifulSoup
from django.utils.text import slugify
from docx import Document
from django.utils.timezone import now

def renomear_imagem_capa(instance, filename):
    base, ext = os.path.splitext(filename)
    nome_base = slugify(instance.slug or instance.titulo or uuid.uuid4().hex[:8])
    novo_nome = f"{nome_base}-capa{ext.lower()}"
    return os.path.join('capas', novo_nome)

def renomear_arquivo_word(instance, filename):
    base, ext = os.path.splitext(filename)
    nome_base = slugify(instance.slug or instance.titulo or uuid.uuid4().hex[:10])
    novo_nome = f"{nome_base}{ext.lower()}"
    return os.path.join('uploads', novo_nome)

def gerar_slug(titulo):
    from .models import Artigo
    base_slug = slugify(titulo)
    slug = base_slug
    contador = 1
    while Artigo.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{contador}"
        contador += 1
    return slug

def gerar_titulo_numerado(titulo_base, ordem_por='id'):
    from django.apps import apps
    Artigo = apps.get_model('A_Lei_no_NT', 'Artigo')
    padrao_numerado = re.compile(r' - \d+ de \d+$')
    artigos_com_titulo_base = Artigo.objects.filter(
        titulo__startswith=titulo_base
    ).order_by(ordem_por)

    total = artigos_com_titulo_base.count() + 1
    artigos_limpos = []
    for artigo in artigos_com_titulo_base:
        titulo_sem_num = padrao_numerado.sub('', artigo.titulo).strip()
        artigo.titulo = titulo_sem_num
        artigos_limpos.append(artigo)

    for i, artigo in enumerate(artigos_limpos, start=1):
        artigo.titulo = f"{titulo_base} - {i} de {total}"
        artigo.save()

    return f"{titulo_base} - {total} de {total}"

def detectar_titulo_possivel(paragrafos):
    for paragrafo in paragrafos:
        texto = paragrafo.text.strip()
        if not texto or len(texto) > 120:
            continue
        runs = paragrafo.runs
        for run in runs:
            if run.bold or run.font.size and run.font.size.pt > 14 or run.underline:
                return texto
    return None

def converter_paragrafo_para_html(paragrafo):
    texto_formatado = ''
    for run in paragrafo.runs:
        texto = run.text
        if not texto:
            continue
        if run.bold:
            texto = f'<strong>{texto}</strong>'
        if run.italic:
            texto = f'<em>{texto}</em>'
        if run.underline:
            texto = f'<u>{texto}</u>'
        texto_formatado += texto
    if texto_formatado:
        return f'<p>{texto_formatado}</p>'
    return ''

def docx_para_html(arquivo_word):
    doc = Document(arquivo_word)
    paragrafos = doc.paragraphs
    titulo = detectar_titulo_possivel(paragrafos)
    if not titulo:
        return '', ''
    html = ''
    for paragrafo in paragrafos:
        html += converter_paragrafo_para_html(paragrafo)
    return html, titulo
