import os
import re
import uuid
from bs4 import BeautifulSoup
from django.utils.text import slugify

def docx_para_html(arquivo):
    from docx import Document
    document = Document(arquivo)
    html = ''
    titulo_extraido = ''

    for i, paragrafo in enumerate(document.paragraphs):
        texto = paragrafo.text.strip()
        if not texto:
            continue

        estilo = paragrafo.style.name.lower()
        if not titulo_extraido:
            titulo_extraido = texto  # Primeira linha com texto será o título

        if 'heading' in estilo:
            nivel = ''.join(filter(str.isdigit, estilo)) or '1'
            html += f'<h{nivel}>{texto}</h{nivel}>'
        elif paragrafo.style.name.lower().startswith("list paragraph"):
            html += f'<li>{texto}</li>'  # Isso será refinado depois
        else:
            html += f'<p>{texto}</p>'

    # Refinar listas com <li> dentro de <ul> ou <ol>
    soup = BeautifulSoup(html, 'html.parser')
    novas_tags = []
    lista_atual = []
    for el in soup.contents:
        if el.name == 'li':
            lista_atual.append(el)
        else:
            if lista_atual:
                ul = soup.new_tag('ul')
                for item in lista_atual:
                    ul.append(item)
                novas_tags.append(ul)
                lista_atual = []
            novas_tags.append(el)
    if lista_atual:
        ul = soup.new_tag('ul')
        for item in lista_atual:
            ul.append(item)
        novas_tags.append(ul)

    soup.clear()
    for tag in novas_tags:
        soup.append(tag)

    return str(soup), titulo_extraido

def gerar_slug(texto):
    texto_base = slugify(texto)
    return texto_base[:100]  # Trunca para no máximo 100 caracteres

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
