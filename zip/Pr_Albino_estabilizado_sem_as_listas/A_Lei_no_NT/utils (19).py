from docx import Document
import re
from django.utils.text import slugify
from .models import Autor

def gerar_slug(titulo):
    return slugify(titulo)[:96]

def gerar_titulo_numerado(titulo, existente):
    contador = 2
    novo_titulo = f"{titulo}-{contador}"
    while novo_titulo in existente:
        contador += 1
        novo_titulo = f"{titulo}-{contador}"
    return novo_titulo

def detectar_titulo_possivel(paragrafos):
    for p in paragrafos[:5]:
        texto = ''.join(run.text for run in p.runs).strip()
        if texto and len(texto.split()) <= 12 and p.style.name.startswith('Heading'):
            return texto
    return 'Título não definido'

def detectar_autor_possivel(paragrafos):
    candidatos = []
    for i, p in enumerate(paragrafos[:5]):
        texto = ''.join(run.text for run in p.runs).strip()
        if not texto:
            continue
        alinhado_direita = p.paragraph_format.alignment == 2
        if alinhado_direita and len(texto) <= 100:
            candidatos.append(texto)
    return candidatos[0] if candidatos else None

def is_manual_list(texto):
    return bool(re.match(r"^[-•\*+]|^\(?\d+[.)])|^[a-zA-Z][.)]", texto.strip()))

def aplicar_formatacao_runs(runs):
    html = ''
    for run in runs:
        texto = run.text.replace('\n', '<br>')
        if not texto.strip():
            continue
        if run.bold:
            texto = f"<strong>{texto}</strong>"
        if run.italic:
            texto = f"<em>{texto}</em>"
        if run.underline:
            texto = f"<u>{texto}</u>"
        html += texto
    return html

def docx_para_html(arquivo):
    doc = Document(arquivo)
    paragrafos = doc.paragraphs
    titulo = detectar_titulo_possivel(paragrafos)
    autor_detectado = detectar_autor_possivel(paragrafos)
    html = ''
    lista_aberta = False
    tipo_lista = None

    for p in paragrafos:
        texto = ''.join(run.text for run in p.runs).strip()
        if not texto:
            html += '<br>'
            continue
        if texto == titulo or texto == autor_detectado:
            continue

        if re.match(r'^[-•*+]', texto) or is_manual_list(texto):
            if not lista_aberta:
                html += '<ul>'
                lista_aberta = True
                tipo_lista = 'ul'
            html += f"<li>{aplicar_formatacao_runs(p.runs)}</li>"
            continue
        elif re.match(r'^(\d+|[a-zA-Z]|[ivxlcdmIVXLCDM])[.)]', texto):
            if not lista_aberta or tipo_lista != 'ol':
                if lista_aberta:
                    html += '</ul>' if tipo_lista == 'ul' else '</ol>'
                html += '<ol>'
                lista_aberta = True
                tipo_lista = 'ol'
            html += f"<li>{aplicar_formatacao_runs(p.runs)}</li>"
            continue
        else:
            if lista_aberta:
                html += '</ul>' if tipo_lista == 'ul' else '</ol>'
                lista_aberta = False
            html += f"<p>{aplicar_formatacao_runs(p.runs)}</p>"

    if lista_aberta:
        html += '</ul>' if tipo_lista == 'ul' else '</ol>'

    return html, titulo, autor_detectado