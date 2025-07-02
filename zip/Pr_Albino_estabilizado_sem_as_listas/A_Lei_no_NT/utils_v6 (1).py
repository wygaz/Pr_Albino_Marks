
from docx import Document
from bs4 import BeautifulSoup
from re import split
from unidecode import unidecode

def docx_para_html(arquivo):
    document = Document(arquivo)
    html = ''
    titulo_extraido = ''
    autor_extraido = ''
    buffer_paragrafo = None  # Para unir "1." com linha seguinte

    soup = BeautifulSoup('', 'html.parser')
    lista_atual = []
    tipo_lista = None
    novas_tags = []

    for paragrafo in document.paragraphs:
        texto_completo = ''.join(run.text for run in paragrafo.runs).strip()

        # Detectar título apenas se ainda não foi extraído
        if not titulo_extraido:
            if paragrafo.style.name.lower().startswith('heading') or (paragrafo.runs and any(run.bold for run in paragrafo.runs)):
                if len(texto_completo.split()) <= 12 and paragrafo.runs and any(run.font.size and run.font.size.pt >= 12 for run in paragrafo.runs):
                    titulo_extraido = texto_completo
                    continue  # Não incluir o título no HTML

        # Detectar parágrafo do autor
        if not autor_extraido and texto_completo.lower().startswith("autor:"):
            autor_extraido = texto_completo
            tag = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = autor_extraido
            tag.append(strong)
            novas_tags.append(tag)
            continue  # Não incluir esse parágrafo novamente

        if texto_completo == '':
            if lista_atual:
                nova_lista = soup.new_tag(tipo_lista)
                for item in lista_atual:
                    nova_lista.append(item)
                novas_tags.append(nova_lista)
                lista_atual = []
                tipo_lista = None
            continue

        if texto_completo.startswith(('-', '*', '•')) or texto_completo[:2].isdigit():
            marcador = texto_completo[0]
            texto_item = texto_completo.lstrip('-*•0123456789. ').strip()
            if marcador in ['-', '*', '•']:
                if tipo_lista != 'ul':
                    if lista_atual:
                        nova_lista = soup.new_tag(tipo_lista)
                        for item in lista_atual:
                            nova_lista.append(item)
                        novas_tags.append(nova_lista)
                    lista_atual = []
                    tipo_lista = 'ul'
                li = soup.new_tag("li")
                li.string = texto_item
                lista_atual.append(li)
            elif texto_completo[:2].isdigit() or texto_completo.split('.')[0].isdigit():
                if tipo_lista != 'ol':
                    if lista_atual:
                        nova_lista = soup.new_tag(tipo_lista)
                        for item in lista_atual:
                            nova_lista.append(item)
                        novas_tags.append(nova_lista)
                    lista_atual = []
                    tipo_lista = 'ol'
                li = soup.new_tag("li")
                li.string = texto_item
                lista_atual.append(li)
            continue

        # Parágrafo comum
        tag = soup.new_tag("p")
        for run in paragrafo.runs:
            texto = run.text
            if not texto:
                continue
            sub_tag = soup.new_tag("span")
            if run.bold:
                sub_tag = soup.new_tag("strong")
            elif run.italic:
                sub_tag = soup.new_tag("em")
            elif run.underline:
                sub_tag = soup.new_tag("u")
            sub_tag.string = texto
            tag.append(sub_tag)
        novas_tags.append(tag)

    if lista_atual:
        nova_lista = soup.new_tag(tipo_lista)
        for item in lista_atual:
            nova_lista.append(item)
        novas_tags.append(nova_lista)

    soup.clear()
    for tag in novas_tags:
        soup.append(tag)

    if not titulo_extraido:
        titulo_extraido = "Artigo sem Título"

    return str(soup), titulo_extraido
