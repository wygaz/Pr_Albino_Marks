def docx_para_html(docx_file):
    from docx import Document
    import html
    import re
    from .utils import detectar_titulo_possivel

    doc = Document(docx_file)
    html_content = ""
    titulo_detectado = None
    ignorar_linha_2_autor = False
    paragrafo_index = 0

    for paragrafo in doc.paragraphs:
        texto_completo = paragrafo.text.strip()
        if not texto_completo:
            html_content += "<br>\n"
            paragrafo_index += 1
            continue

        # Verificar se é a 2ª linha "Autor: ..." para ignorar
        if paragrafo_index == 1 and texto_completo.lower().startswith("autor:"):
            ignorar_linha_2_autor = True

        if ignorar_linha_2_autor:
            ignorar_linha_2_autor = False
            paragrafo_index += 1
            continue

        # Detectar possível título apenas se ainda não foi encontrado
        if not titulo_detectado:
            titulo_detectado = detectar_titulo_possivel(texto_completo)

        # Verificar se é uma lista manual
        match = re.match(r"^(\d+[\.\)]|\•|\*|\-)\s*", texto_completo)
        if match:
            prefixo = match.group(0)
            restante = texto_completo[len(prefixo):]

            texto_formatado = ""
            for run in paragrafo.runs:
                trecho = html.escape(run.text)
                if run.bold:
                    trecho = f"<strong>{trecho}</strong>"
                if run.italic:
                    trecho = f"<em>{trecho}</em>"
                if run.underline:
                    trecho = f"<u>{trecho}</u>"
                texto_formatado += trecho

            texto_formatado = texto_formatado.strip()

            html_content += f"<p>{html.escape(prefixo)}&nbsp;{texto_formatado}</p>\n"
        else:
            texto_formatado = ""
            for run in paragrafo.runs:
                trecho = html.escape(run.text)
                if run.bold:
                    trecho = f"<strong>{trecho}</strong>"
                if run.italic:
                    trecho = f"<em>{trecho}</em>"
                if run.underline:
                    trecho = f"<u>{trecho}</u>"
                texto_formatado += trecho

            texto_formatado = texto_formatado.strip()
            html_content += f"<p>{texto_formatado}</p>\n"

        paragrafo_index += 1

    return html_content.strip(), titulo_detectado