
import re
from bs4 import BeautifulSoup
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import unicodedata

def gerar_slug(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto).strip().lower()
    return re.sub(r'[-\s]+', '-', texto)

def gerar_titulo_numerado(titulo, numero):
    return f"{numero:02d} - {titulo}"

def detectar_titulo_possivel(paragrafos):
    for p in paragrafos[:5]:
        texto = ''.join(run.text for run in p.runs).strip()
        if texto and len(texto.split()) <= 12 and p.style.name.startswith('Heading'):
            return texto
    return ''

def detectar_autor_por_base(paragrafos, nomes_autores_bd):
    for p in paragrafos[:5]:
        texto = ''.join(run.text for run in p.runs).strip()
        if not texto:
            continue
        texto_limpo = re.sub(r'^Autor:\s*', '', texto, flags=re.IGNORECASE).strip()
        if texto_limpo in nomes_autores_bd:
            return texto_limpo
        if p.alignment == WD_PARAGRAPH_ALIGNMENT.RIGHT and texto_limpo in nomes_autores_bd:
            return texto_limpo
    return None

def docx_para_html(arquivo, nomes_autores_bd):
    doc = Document(arquivo)
    paragrafos = doc.paragraphs
    html = ''

    titulo = detectar_titulo_possivel(paragrafos)
    autor = detectar_autor_por_base(paragrafos, nomes_autores_bd)

    if titulo:
        html += f'<h1 style="text-align: center;">{titulo}</h1>\n'

    if autor:
        html += f'<p style="text-align: right;"><strong>{autor}</strong></p>\n'

    for p in paragrafos:
        texto_completo = ''.join(run.text for run in p.runs).strip()

        if texto_completo.startswith("Autor:") or texto_completo == autor:
            continue

        if texto_completo.startswith('- '):
            html += f'<ul><li>{texto_completo[2:].strip()}</li></ul>\n'
            continue

        if re.match(r'^\d+[\.\-–)]?\s', texto_completo):
            partes = texto_completo.split(maxsplit=1)
            if len(partes) == 2:
                numero, conteudo = partes
                html += f'<ol><li>{conteudo.strip()}</li></ol>\n'
            else:
                html += f'<ol><li>{texto_completo.strip()}</li></ol>\n'
            continue

        if texto_completo:
            texto_formatado = ''
            for run in p.runs:
                t = run.text.replace('\xa0', '&nbsp;')
                if run.bold:
                    t = f"<strong>{t}</strong>"
                if run.italic:
                    t = f"<em>{t}</em>"
                if run.underline:
                    t = f"<u>{t}</u>"
                texto_formatado += t
            html += f'<p>{texto_formatado}</p>\n'

    return html, titulo
