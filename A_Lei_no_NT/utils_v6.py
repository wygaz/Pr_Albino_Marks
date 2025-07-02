from docx import Document
from bs4 import BeautifulSoup
from re import split

def docx_para_html(arquivo):
    document = Document(arquivo)
    soup = BeautifulSoup("", "html.parser")
    titulo_extraido = ""
    titulo_definido = False
    autor_processado = False
    novas_tags = []
    lista_atual = []
    tipo_lista = None
    buffer_paragrafo = None

    def aplicar_formatacoes(texto, negrito=False, italico=False, sublinhado=False):
        if not texto:
            return ""
        if negrito:
            texto = f"<strong>{texto}</strong>"
        if italico:
            texto = f"<em>{texto}</em>"
        if sublinhado:
            texto = f"<u>{texto}</u>"
        return texto

    for paragrafo in document.paragraphs:
        if paragrafo.style.name == "Normal" and not paragrafo.text.strip():
            continue

        texto = "".join(run.text for run in paragrafo.runs).strip()

        if not texto:
            continue

        # Detectar TÍTULO baseado em formatação
        if not titulo_definido:
            for run in paragrafo.runs:
                if run.bold and run.font.size and run.font.size.pt > 12:
                    titulo_extraido = texto
                    titulo_definido = True
                    break

        # Detectar AUTOR
        if not autor_processado:
            texto_unificado = "".join(run.text for run in paragrafo.runs).strip()
            if texto_unificado.lower().startswith("autor:"):
                p_autor = soup.new_tag("p")
                p_autor.append(BeautifulSoup(f"<strong>{texto_unificado}</strong>", "html.parser"))
                novas_tags.append(p_autor)
                autor_processado = True
                continue

        # Quebra de página manual
        if "====================" in texto:
            hr = soup.new_tag("hr", attrs={"class": "page-break"})
            novas_tags.append(hr)
            continue

        # Lista ordenada manual
        if texto.lstrip().startswith(tuple(str(i) for i in range(1, 10))) and "–" in texto:
            if tipo_lista != "ol":
                if lista_atual:
                    nova_lista = soup.new_tag(tipo_lista)
                    for item in lista_atual:
                        nova_lista.append(item)
                    novas_tags.append(nova_lista)
                lista_atual = []
                tipo_lista = "ol"
            li = soup.new_tag("li")
            li.append(texto.split("–", 1)[1].strip())
            lista_atual.append(li)
            continue

        # Lista não ordenada manual
        if texto.lstrip().startswith("-"):
            if tipo_lista != "ul":
                if lista_atual:
                    nova_lista = soup.new_tag(tipo_lista)
                    for item in lista_atual:
                        nova_lista.append(item)
                    novas_tags.append(nova_lista)
                lista_atual = []
                tipo_lista = "ul"
            li = soup.new_tag("li")
            li.append(texto.lstrip("-").strip())
            lista_atual.append(li)
            continue

        # Parágrafo normal com formatação
        p = soup.new_tag("p")
        for run in paragrafo.runs:
            texto_run = run.text
            if not texto_run:
                continue
            html_formatado = aplicar_formatacoes(
                texto_run,
                negrito=run.bold,
                italico=run.italic,
                sublinhado=run.underline
            )
            p.append(BeautifulSoup(html_formatado, "html.parser"))
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
