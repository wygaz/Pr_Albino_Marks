
from docx import Document
from bs4 import BeautifulSoup
import re

def docx_para_html(arquivo):
    document = Document(arquivo)
    soup = BeautifulSoup('', 'html.parser')
    titulo_extraido = ''
    autor_extraido = ''
    novas_tags = []
    lista_atual = []
    tipo_lista = None
    dentro_de_lista_manual = False
    buffer_paragrafo = None

    def espaco_incondicional(texto):
        return texto.replace(' ', ' ')

    def aplicar_formatacao(run):
        texto = espaco_incondicional(run.text)
        if not texto:
            return ''
        if run.bold:
            texto = f'<strong>{texto}</strong>'
        if run.italic:
            texto = f'<em>{texto}</em>'
        if run.underline:
            texto = f'<u>{texto}</u>'
        return texto

    def is_lista_manual(paragrafo):
        texto = ''.join(run.text for run in paragrafo.runs).strip()
        return bool(re.match(r'^[-–*•]\s+.+', texto)) or bool(re.match(r'^\d+[).]\s+.+', texto))

    def criar_item_lista(paragrafo):
        texto_formatado = ''.join(aplicar_formatacao(run) for run in paragrafo.runs).strip()
        li = soup.new_tag("li")
        li.append(BeautifulSoup(texto_formatado, 'html.parser'))
        return li

    for paragrafo in document.paragraphs:
        texto_completo = ''.join(run.text for run in paragrafo.runs).strip()
        if not texto_completo:
            continue

        if not titulo_extraido:
            titulo_extraido = texto_completo
            continue

        if texto_completo.lower().startswith("autor:"):
            autor_extraido = texto_completo
            continue

        if is_lista_manual(paragrafo):
            if not dentro_de_lista_manual:
                dentro_de_lista_manual = True
                if re.match(r'^\d+[).]', texto_completo):
                    tipo_lista = 'ol'
                else:
                    tipo_lista = 'ul'
                lista_atual = []
            item = criar_item_lista(paragrafo)
            lista_atual.append(item)
            continue
        else:
            if dentro_de_lista_manual:
                nova_lista = soup.new_tag(tipo_lista)
                for item in lista_atual:
                    nova_lista.append(item)
                novas_tags.append(nova_lista)
                lista_atual = []
                tipo_lista = None
                dentro_de_lista_manual = False

        html_paragrafo = ''.join(aplicar_formatacao(run) for run in paragrafo.runs).strip()
        if html_paragrafo:
            p_tag = soup.new_tag('p')
            p_tag.append(BeautifulSoup(html_paragrafo, 'html.parser'))
            novas_tags.append(p_tag)

    if dentro_de_lista_manual:
        nova_lista = soup.new_tag(tipo_lista)
        for item in lista_atual:
            nova_lista.append(item)
        novas_tags.append(nova_lista)

    if not titulo_extraido:
        titulo_extraido = "Artigo sem Título"

    soup.clear()
    for tag in novas_tags:
        soup.append(tag)

    return str(soup), titulo_extraido
