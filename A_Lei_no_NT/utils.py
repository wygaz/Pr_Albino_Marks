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
