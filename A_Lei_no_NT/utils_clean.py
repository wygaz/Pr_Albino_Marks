import os
import re
import unicodedata
from bs4 import BeautifulSoup
from django.utils.text import slugify
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def gerar_slug(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto).strip().lower()
    return re.sub(r'[-\s]+', '-', texto)

def gerar_titulo_numerado(titulo, numero):
    return f"{numero:02d} - {titulo}"

def detectar_titulo_possivel(paragrafos):
    for i, p in enumerate(paragrafos[:5]):
        texto = ''.join(run.text for run in p.runs).strip()
        if texto and len(texto.split()) <= 12 and p.style.name.startswith('Heading'):
            return texto
    return ''

def detectar_autor(paragrafos):
    for i, p in enumerate(paragrafos[:5]):
        texto = ''.join(run.text for run in p.runs).strip()
        if not texto:
            continue
        if texto.lower().startswith("autor:"):
            return re.sub(r'^Autor:\s*', '', texto, flags=re.IGNORECASE).strip()
        elif p.alignment == WD_PARAGRAPH_ALIGNMENT.RIGHT:
            if len(texto.split()) <= 6:
                return texto
    return None

def renomear_arquivo_word(arquivo):
    nome = os.path.splitext(arquivo.name)[0]
    nome_slug = gerar_slug(nome)
    extensao = os.path.splitext(arquivo.name)[1]
    novo_nome = f"{nome_slug}{extensao}"
    return novo_nome

def docx_para_html(arquivo):
    doc = Document(arquivo)
    paragrafos = doc.paragraphs
    html = ''

    titulo = detectar_titulo_possivel(paragrafos)
    autor = detectar_autor(paragrafos)

    if titulo:
        html += f'<h1 style="text-align: center;">{titulo}</h1>\n'

    if autor:
        html += f'<p style="text-align: right;"><strong>{autor}</strong></p>\n'

    skip_texts = set()
    if titulo:
        skip_texts.add(titulo.strip())
    if autor:
        skip_texts.add("Autor:")
        skip_texts.add(autor.strip())

    for p in paragrafos:
        texto = ''.join(run.text for run in p.runs).strip()
        if not texto or texto in skip_texts:
            continue

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

        # Detecção de listas manuais e automáticas
        if texto.startswith('- '):
            html += f'<ul><li>{texto_formatado[2:].strip()}</li></ul>\n'
        elif re.match(r'^[\dIVXLCDM]+[\.\-–\)]\s+', texto):
            item = re.sub(r'^[\dIVXLCDM]+[\.\-–\)]\s+', '', texto_formatado)
            html += f'<ol><li>{item}</li></ol>\n'
        elif texto_formatado.lower() in ['fruto do espírito', 'dons espirituais', 'serviços cristãos',
                                         'amar a deus', 'amar o próximo', 'guardar os mandamentos']:
            html += f'<ul><li>{texto_formatado}</li></ul>\n'
        elif '|' in texto:
            colunas = texto.split('|')
            html += '<table><tr>' + ''.join(f'<td>{c.strip()}</td>' for c in colunas if c.strip()) + '</tr></table>\n'
        elif '\n' in texto:
            partes = texto.split('\n')
            html += ''.join(f'<p>{parte.strip()}</p>\n' for parte in partes)
        else:
            html += f'<p>{texto_formatado}</p>\n'
    return html, titulo