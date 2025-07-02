from docx import Document
from bs4 import BeautifulSoup
import re

def docx_para_html(arquivo):
    document = Document(arquivo)
    soup = BeautifulSoup(features="html.parser")
    titulo_extraido = ""
    autor_extraido = ""
    novas_tags = []
    lista_atual = []
    tipo_lista = None
    buffer_paragrafo = None
    titulo_capturado = False
    autor_detectado = False

    def run_para_html(run):
        texto = run.text
        if not texto.strip():
            return ''
        if run.bold:
            texto = f"<strong>{texto}</strong>"
        if run.italic:
            texto = f"<em>{texto}</em>"
        if run.underline:
            texto = f"<u>{texto}</u>"
        return texto

    for paragrafo in document.paragraphs:
        texto_completo = ''.join(run.text for run in paragrafo.runs).strip()

        if not texto_completo:
            continue

        # Detectar título
        if not titulo_capturado:
            tamanho_fonte_maior = any(
                run.font.size and run.font.size.pt > 12 for run in paragrafo.runs
            )
            if (paragrafo.style.name.lower().startswith("heading")
                    or tamanho_fonte_maior
                    or all(run.bold for run in paragrafo.runs if run.text.strip())):
                titulo_extraido = texto_completo
                titulo_capturado = True
                continue  # não renderiza título no HTML

        # Detectar autor
        if not autor_detectado and texto_completo.lower().startswith("autor:"):
            autor_extraido = texto_completo
            autor_tag = soup.new_tag("p")
            autor_tag.append(soup.new_tag("strong"))
            autor_tag.strong.string = autor_extraido
            novas_tags.append(autor_tag)
            autor_detectado = True
            continue

# Identificação de listas manualmente formatadas
        if texto_completo.startswith("- ") or texto_completo.startswith("• "):
            if tipo_lista != 'ul':
                if lista_atual:
                    nova_lista = soup.new_tag(tipo_lista)
                    for item in lista_atual:
                        nova_lista.append(item)
                    novas_tags.append(nova_lista)
                    lista_atual = []
                tipo_lista = 'ul'
            li = soup.new_tag("li")
            li.string = texto_completo[2:].strip()
            lista_atual.append(li)
            continue
        elif re.match(r'^\d+\.', texto_completo):
            if tipo_lista != 'ol':
                if lista_atual:
                    nova_lista = soup.new_tag(tipo_lista)
                    for item in lista_atual:
                        nova_lista.append(item)
                    novas_tags.append(nova_lista)
                    lista_atual = []
                tipo_lista = 'ol'
            li = soup.new_tag("li")
            li.string = texto_completo[texto_completo.find('.') + 1:].strip()
            lista_atual.append(li)
            continue
        else:
            if lista_atual:
                nova_lista = soup.new_tag(tipo_lista)
                for item in lista_atual:
                    nova_lista.append(item)
                novas_tags.append(nova_lista)
                lista_atual = []
                tipo_lista = None

        # Formatação comum de parágrafos com runs
        p = soup.new_tag("p")
        for run in paragrafo.runs:
            html_run = run_para_html(run)
            if html_run:
                p.append(BeautifulSoup(html_run, "html.parser"))
        novas_tags.append(p)

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