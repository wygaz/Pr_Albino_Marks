from docx import Document
from docx.text.paragraph import Paragraph
from django.utils.text import slugify
from datetime import datetime

def gerar_slug(titulo):
    return slugify(titulo)

def gerar_titulo_numerado(titulo_base, total):
    return f"{titulo_base} - {total} de {total}"

def detectar_titulo_possivel(paragrafos):
    for p in paragrafos[:5]:
        texto = "".join(run.text for run in p.runs).strip()
        if len(texto.split()) <= 12 and texto.lower().startswith("artigo"):
            return texto
    return None

def docx_para_html(file):
    document = Document(file)
    html = ""
    titulo = None
    autor_detectado = False
    autor_ja_adicionado = False
    ignorar_paragrafos = set()

    paragrafos = document.paragraphs

    # Tentativa de detecção de título
    titulo_possivel = detectar_titulo_possivel(paragrafos)
    if titulo_possivel:
        titulo = titulo_possivel

    for idx, p in enumerate(paragrafos):
        texto_completo = "".join(run.text for run in p.runs).strip()

        if not texto_completo:
            continue

        if not autor_detectado and texto_completo.lower().startswith("autor:"):
            if not autor_ja_adicionado:
                html += f"<p><strong>{texto_completo}</strong></p>
"
                autor_ja_adicionado = True
                ignorar_paragrafos.add(idx)
            autor_detectado = True
            continue

        if idx in ignorar_paragrafos:
            continue

        if p.style.name.startswith("Heading"):
            nivel = p.style.name[-1]
            html += f"<h{nivel}>{texto_completo}</h{nivel}>
"
        elif p.style.name == "List Paragraph":
            if texto_completo[0].isdigit():
                html += f"<ol><li>{texto_completo}</li></ol>
"
            else:
                html += f"<ul><li>{texto_completo}</li></ul>
"
        else:
            negrito = any(run.bold for run in p.runs)
            italico = any(run.italic for run in p.runs)
            sublinhado = any(run.underline for run in p.runs)

            estilo = ""
            if negrito:
                estilo += "<strong>"
            if italico:
                estilo += "<em>"
            if sublinhado:
                estilo += "<u>"

            fim_estilo = ""
            if sublinhado:
                fim_estilo = "</u>" + fim_estilo
            if italico:
                fim_estilo = "</em>" + fim_estilo
            if negrito:
                fim_estilo = "</strong>" + fim_estilo

            html += f"<p>{estilo}{texto_completo}{fim_estilo}</p>
"

    if not autor_detectado:
        print("⚠️ Nenhum autor foi detectado no documento.")

    return html, titulo
