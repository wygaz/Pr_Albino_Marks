
from docx import Document
from bs4 import BeautifulSoup
import re

def docx_para_html(arquivo):
    document = Document(arquivo)
    soup = BeautifulSoup("", "html.parser")
    titulo_extraido = None
    possiveis_autores = []
    novos_elementos = []
    buffer_paragrafo = None

    autores_cadastrados = [
        "Pr. Albino Marks", "Albino Marks", "Albino M.", "Pr. A. Marks"
    ]

    def limpar_texto_runs(paragrafo):
        return "".join([r.text.strip() for r in paragrafo.runs]).strip()

    def formatar_runs(paragrafo):
        partes = []
        for run in paragrafo.runs:
            texto = run.text.replace("\xa0", " ")
            if not texto:
                continue
            if run.bold:
                texto = f"<strong>{texto}</strong>"
            if run.italic:
                texto = f"<em>{texto}</em>"
            if run.underline:
                texto = f"<u>{texto}</u>"
            partes.append(texto)
        return " ".join(partes).strip()

    for i, paragrafo in enumerate(document.paragraphs):
        texto = limpar_texto_runs(paragrafo)
        if not texto:
            continue

        alinhamento = getattr(paragrafo.paragraph_format.alignment, "name", "").lower()

        if not titulo_extraido:
            fonte_maior = any(r.font.size and r.font.size.pt > 12 for r in paragrafo.runs)
            if fonte_maior:
                titulo_extraido = texto
                continue

        if i in (1, 2):
            if alinhamento == "right" or len(texto) <= 100:
                if any(autor in texto for autor in autores_cadastrados):
                    possiveis_autores.append(texto)
                    continue

        texto_formatado = formatar_runs(paragrafo)
        p_tag = soup.new_tag("p")
        p_tag.append(BeautifulSoup(texto_formatado, "html.parser"))
        novos_elementos.append(p_tag)

    if not titulo_extraido:
        titulo_extraido = "Artigo sem Título"

    soup.clear()
    for tag in novos_elementos:
        soup.append(tag)

    return str(soup), titulo_extraido
