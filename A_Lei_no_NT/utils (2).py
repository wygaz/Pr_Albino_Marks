
from docx import Document
import re
from io import BytesIO

def gerar_slug(texto):
    return re.sub(r'[^a-z0-9]+', '-', texto.lower()).strip('-')

def remover_simbologia_manual(texto):
    return re.sub(r'^[\-*•\u2022\u25CF\u25CB\u25A0\u25E6\u2219\u2043\u25AA\u25AB\u25AC\u25AD\u25FE\u25FD]+\s*', '', texto)

def docx_para_html(arquivo_docx):
    doc = Document(BytesIO(arquivo_docx.read()))
    html = ''
    titulo = None

    lista_atual = []
    tipo_lista_atual = None
    nivel_anterior = 0

    def fechar_lista():
        nonlocal html, lista_atual, tipo_lista_atual
        if lista_atual:
            tag = 'ol' if tipo_lista_atual == 'ordenada' else 'ul'
            html += f"<{tag}>" + ''.join(lista_atual) + f"</{tag}>"
            lista_atual = []
            tipo_lista_atual = None

    def identificar_lista_manual(paragrafo):
        texto = paragrafo.text.strip()
        match = re.match(r'^([0-9]+[a-zA-Z]?|[a-zA-Z]\.)\s+', texto)
        if match:
            return 'ordenada'
        elif texto.startswith(('-', '*', '•')):
            return 'nao_ordenada'
        return None

    def identificar_nivel(paragrafo):
        return paragrafo.paragraph_format.left_indent.pt if paragrafo.paragraph_format.left_indent else 0

    for paragrafo in doc.paragraphs:
        estilo = paragrafo.style.name.lower()
        texto = paragrafo.text.strip()

        if not texto:
            fechar_lista()
            html += '<br>'
            continue

        if not titulo and estilo.startswith('heading'):
            titulo = texto
            html += f"<h2>{texto}</h2>"
            continue

        tipo_manual = identificar_lista_manual(paragrafo)
        is_lista_nativa = estilo.startswith('list')
        nivel_atual = identificar_nivel(paragrafo)

        if is_lista_nativa or tipo_manual:
            tipo_lista = 'ordenada' if 'number' in estilo or tipo_manual == 'ordenada' else 'nao_ordenada'

            if tipo_lista != tipo_lista_atual or nivel_atual != nivel_anterior:
                fechar_lista()
                tipo_lista_atual = tipo_lista

            texto_sem_marcador = remover_simbologia_manual(texto)
            nivel_html = ' style="margin-left:{}em;"'.format(nivel_atual / 10 if nivel_atual > 0 else 0)
            lista_atual.append(f'<li{nivel_html}>{texto_sem_marcador}</li>')
            nivel_anterior = nivel_atual
        else:
            fechar_lista()
            html += f'<p>{texto}</p>'

    fechar_lista()
    if not titulo:
        titulo = 'Sem Título'
    return html, titulo
