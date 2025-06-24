from docx import Document
import unicodedata
import re
import os
from django.utils.text import slugify


def docx_para_html(docx_file):
    def trata_run(run):
        texto = run.text.replace('\n', '<br>')
        if not texto.strip():
            return ''
        if run.bold:
            texto = f"<strong>{texto}</strong>"
        if run.italic:
            texto = f"<em>{texto}</em>"
        if run.underline:
            texto = f"<u>{texto}</u>"
        return texto

    def processa_paragrafo(paragrafo):
        estilo = paragrafo.style.name.lower()
        texto_processado = ''.join([trata_run(run) for run in paragrafo.runs])

        # Remove hífens ou marcadores iniciais (como • - etc)
        texto_sem_hifen = re.sub(r'^[\-\–\—\•\·‒‧\u2022\s]+', '', texto_processado).strip()

        if estilo.startswith('heading 1'):
            return f'<h2>{texto_sem_hifen}</h2>'
        elif estilo.startswith('heading 2'):
            return f'<h3>{texto_sem_hifen}</h3>'
        elif estilo in (
            'list paragraph', 'lista com marcadores', 'list number', 'lista numerada'
        ) or paragrafo.text.strip().startswith(('-', '•', '·', '‣')):
            return f'<li>{texto_sem_hifen}</li>'
        else:
            return f'<p>{texto_processado}</p>'

    document = Document(docx_file)
    html_partes = []
    lista_ul_aberta = False
    lista_ol_aberta = False
    titulo_extraido = None

    for paragrafo in document.paragraphs:
        estilo = paragrafo.style.name.lower()

        if not titulo_extraido and estilo.startswith('heading 1') and paragrafo.text.strip():
            # Remove hífens e espaços inúteis do título
            titulo_extraido = re.sub(r'^[\-\–\—\•\·‒‧\u2022\s]+', '', paragrafo.text.strip()).strip()

        if estilo in ('list paragraph', 'lista com marcadores') or paragrafo.text.strip().startswith(('•', '·', '‣', '-')):
            if not lista_ul_aberta:
                if lista_ol_aberta:
                    html_partes.append('</ol>')
                    lista_ol_aberta = False
                html_partes.append('<ul>')
                lista_ul_aberta = True
            html_partes.append(processa_paragrafo(paragrafo))
        elif estilo in ('list number', 'lista numerada'):
            if not lista_ol_aberta:
                if lista_ul_aberta:
                    html_partes.append('</ul>')
                    lista_ul_aberta = False
                html_partes.append('<ol>')
                lista_ol_aberta = True
            html_partes.append(processa_paragrafo(paragrafo))
        else:
            if lista_ul_aberta:
                html_partes.append('</ul>')
                lista_ul_aberta = False
            if lista_ol_aberta:
                html_partes.append('</ol>')
                lista_ol_aberta = False
            html_partes.append(processa_paragrafo(paragrafo))

    if lista_ul_aberta:
        html_partes.append('</ul>')
    if lista_ol_aberta:
        html_partes.append('</ol>')

    conteudo_html = '<html><head><meta charset="UTF-8"></head><body>' + '\n'.join(html_partes) + '</body></html>'

    # print para depuração — você pode comentar depois
    print(f"Título extraído do .docx: {titulo_extraido}")

    return conteudo_html, titulo_extraido


def gerar_slug(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto).strip().lower()
    return re.sub(r'[-\s]+', '-', texto)


def renomear_imagem_capa(instance, filename):
    base, ext = os.path.splitext(filename)
    slug = slugify(instance.titulo or "sem-titulo")
    return f"imagens/artigos/{slug}{ext}"
