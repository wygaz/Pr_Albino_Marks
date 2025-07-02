
import re
from bs4 import BeautifulSoup
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from django.utils.text import slugify

def gerar_slug(texto):
    return slugify(texto)

def gerar_titulo_numerado(titulo, numero):
    return f"{numero:02d} - {titulo}"

def detectar_titulo_possivel(paragrafos):
    for p in paragrafos[:5]:
        texto = ''.join(run.text for run in p.runs).strip()
        if texto and len(texto.split()) <= 12 and p.style.name.startswith('Heading'):
            return texto
    return ''

def detectar_autor_por_padrao(paragrafos):
    nomes_autores_conhecidos = [
        'Pr. Rubens Flores', 'Prof. Rubens Flores',
        'Fulano de Tal', 'Pr. Albino Marks', 'Wanderley Gazeta'
    ]
    for p in paragrafos[:5]:
        texto = ''.join(run.text for run in p.runs).strip()
        if not texto:
            continue
        texto_limpo = re.sub(r'^Autor:\s*', '', texto, flags=re.IGNORECASE).strip()
        if texto_limpo in nomes_autores_conhecidos:
            return texto_limpo
        if p.alignment == WD_PARAGRAPH_ALIGNMENT.RIGHT and texto_limpo:
            return texto_limpo
    return None

def docx_para_html(arquivo):
    doc = Document(arquivo)
    paragrafos = doc.paragraphs
    html = ''

    titulo = detectar_titulo_possivel(paragrafos)
    autor = detectar_autor_por_padrao(paragrafos)

    if titulo:
        html += f'<h1 style="text-align: center;">{titulo}</h1>\n'

    if autor:
        html += f'<p style="text-align: right;"><strong>{autor}</strong></p>\n'

    lista_aberta = False
    lista_tipo = None

    for p in paragrafos:
        texto = ''.join(run.text for run in p.runs).strip()
        if not texto:
            continue

        if texto.startswith('Autor:') or texto.strip() == autor:
            continue

        if texto.startswith('- '):
            if lista_tipo != 'ul':
                if lista_aberta:
                    html += f'</{lista_tipo}>\n'
                html += '<ul>\n'
                lista_aberta = True
                lista_tipo = 'ul'
            html += f'<li>{texto[2:].strip()}</li>\n'

        elif re.match(r'^\d+[\.\-–)]?\s', texto):
            if lista_tipo != 'ol':
                if lista_aberta:
                    html += f'</{lista_tipo}>\n'
                html += '<ol>\n'
                lista_aberta = True
                lista_tipo = 'ol'
            html += f'<li>{texto}</li>\n'

        else:
            if lista_aberta:
                html += f'</{lista_tipo}>\n'
                lista_aberta = False
                lista_tipo = None
            texto_formatado = ''
            for run in p.runs:
                t = run.text.replace('\xa0', '&nbsp;')
                if run.bold:
                    t = f'<strong>{t}</strong>'
                if run.italic:
                    t = f'<em>{t}</em>'
                if run.underline:
                    t = f'<u>{t}</u>'
                texto_formatado += t
            html += f'<p>{texto_formatado}</p>\n'

    if lista_aberta:
        html += f'</{lista_tipo}>\n'

    return html, titulo
