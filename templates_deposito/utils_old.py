import os
import re
import uuid
from bs4 import BeautifulSoup
from django.utils.text import slugify

from docx import Document
from io import BytesIO

def docx_para_html(arquivo):
    document = Document(BytesIO(arquivo.read()))
    html = ""
    titulo = ""
    dentro_ul = False
    dentro_ol = False

    for par in document.paragraphs:
        texto = par.text.strip()

        if not texto:
            continue

        # Título
        if not titulo:
            titulo = texto

        # Listas não ordenadas
        elif texto.startswith(("•", "-", "–")):
            if not dentro_ul:
                html += "<ul>\n"
                dentro_ul = True
            html += f"<li>{texto[1:].strip()}</li>\n"

        # Listas ordenadas
        elif texto[:2].isdigit() and texto[2:3] in (".", ")"):
            if not dentro_ol:
                html += "<ol>\n"
                dentro_ol = True
            html += f"<li>{texto[3:].strip()}</li>\n"

        else:
            # Fecha listas se estiverem abertas
            if dentro_ul:
                html += "</ul>\n"
                dentro_ul = False
            if dentro_ol:
                html += "</ol>\n"
                dentro_ol = False

            html += f"<p>{texto}</p>\n"

    # Fecha qualquer lista aberta ao final
    if dentro_ul:
        html += "</ul>\n"
    if dentro_ol:
        html += "</ol>\n"

    return html, titulo


import re  # no topo, se ainda não estiver

def gerar_titulo_numerado(titulo_base, ordem_por='id'):
    from django.apps import apps
    Artigo = apps.get_model('A_Lei_no_NT', 'Artigo')

    # Padrão para identificar numeração no final
    padrao_numerado = re.compile(r' - \d+ de \d+$')

    # Buscar todos os artigos que compartilham o mesmo título base
    artigos_com_titulo_base = Artigo.objects.filter(
        titulo__startswith=titulo_base
    ).order_by(ordem_por)

    # Verifica se o novo artigo já existe (evita duplicação)
    total = artigos_com_titulo_base.count() + 1

    # Remove numeração dos anteriores antes de renumerar
    artigos_limpos = []
    for artigo in artigos_com_titulo_base:
        titulo_sem_num = padrao_numerado.sub('', artigo.titulo).strip()
        artigo.titulo = titulo_sem_num
        artigos_limpos.append(artigo)

    # Renumera os anteriores com base no novo total
    for i, artigo in enumerate(artigos_limpos, start=1):
        artigo.titulo = f"{titulo_base} - {i} de {total}"
        artigo.save()

    # Retorna o título numerado do novo artigo
    return f"{titulo_base} - {total} de {total}"


def gerar_slug(titulo):
    from .models import Artigo  # ✅ Importação local para evitar ciclo

    base_slug = slugify(titulo)
    slug = base_slug
    contador = 1
    while Artigo.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{contador}"
        contador += 1
    return slug

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
