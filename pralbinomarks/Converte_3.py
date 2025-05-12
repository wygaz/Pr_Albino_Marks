from docx import Document
from docx.shared import Pt

def docx_to_html(docx_path):
    doc = Document(docx_path)
    html_content = ""

    for para in doc.paragraphs:
        html_content += "<p>"
        for run in para.runs:
            if run.bold:
                html_content += f"<strong>{run.text}</strong>"
            elif run.italic:
                html_content += f"<em>{run.text}</em>"
            else:
                html_content += run.text
        html_content += "</p>\n"

    return html_content

# Caminho para o seu arquivo DOCX
docx_path = r"C:\Users\Wanderley\Documents\Textos_Pr_Albino\1_OS_ESCRITORES_DO_NT_E_A_lei.docx"
html_content = docx_to_html(docx_path)

# Salve o conteúdo HTML em um arquivo
with open(r"C:\Users\Wanderley\Documents\Textos_Pr_Albino\1_OS_ESCRITORES_DO_NT_E_A_lei.html", "w", encoding="utf-8") as f:
    f.write(html_content)
