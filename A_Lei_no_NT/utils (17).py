from docx import Document
import re
from django.utils.text import slugify

def gerar_slug(titulo):
    return slugify(titulo)

def gerar_titulo_numerado(numero):
    return f"Artigo sem título #{numero}"

def detectar_titulo_possivel(paragrafos):
    for p in paragrafos:
        texto = "".join(run.text for run in p.runs).strip()
        if p.style.name.startswith('Heading') and texto:
            return texto
        if len(texto) > 10 and texto.isupper():
            return texto
        if p.style.name == 'Title':
            return texto
    return None

def aplicar_formatacao(run):
    texto = run.text.replace("\n", "<br>")

    if not texto.strip():
        return ""

    if run.bold:
        texto = f"<strong>{texto}</strong>"
    if run.italic:
        texto = f"<em>{texto}</em>"
    if run.underline:
        texto = f"<u>{texto}</u>"

    return texto

def docx_para_html(arquivo):
    doc = Document(arquivo)
    paragrafos = doc.paragraphs

    html = ""
    titulo = detectar_titulo_possivel(paragrafos)
    if not titulo:
        titulo = "Artigo sem título"

    lista_aberta = False
    lista_tipo = None
    pilha_listas = []

    for p in paragrafos:
        estilo = p.style.name
        texto = "".join([aplicar_formatacao(run) for run in p.runs]).strip()

        if not texto:
            continue

        # LISTAS
        if "ListBullet" in estilo or "ListNumber" in estilo:
            tipo_atual = "ul" if "Bullet" in estilo else "ol"
            nivel = int(re.findall(r'\d+', estilo[-1])[-1]) if estilo[-1].isdigit() else 1

            # Ajuste da pilha de listas
            while len(pilha_listas) > nivel:
                html += f"</{pilha_listas.pop()}>\n"

            while len(pilha_listas) < nivel:
                html += f"<{tipo_atual}>\n"
                pilha_listas.append(tipo_atual)

            html += f"<li>{texto}</li>\n"
            continue

        else:
            # Fecha qualquer lista aberta
            while pilha_listas:
                html += f"</{pilha_listas.pop()}>\n"

        # PARÁGRAFO PADRÃO
        html += f"<p>{texto}</p>\n"

    # Fecha listas não encerradas
    while pilha_listas:
        html += f"</{pilha_listas.pop()}>\n"

    return html.strip(), titulo
