import os
from docx import Document

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

def convert_all_docx_to_html(input_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(input_directory):
        if filename.endswith(".docx"):
            docx_path = os.path.join(input_directory, filename)
            html_content = docx_to_html(docx_path)
            html_filename = os.path.splitext(filename)[0] + ".html"
            html_path = os.path.join(output_directory, html_filename)

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

# Caminho para o diretório com arquivos DOCX
input_directory = r"C:\Users\Wanderley\Apps\Albino_Marks\A_Lei_no_NT\Templates\A_Lei_no_NT\Textos\DOCX"
# Caminho para o diretório onde os arquivos HTML serão salvos
output_directory = r"C:\Users\Wanderley\Apps\Albino_Marks\A_Lei_no_NT\Templates\A_Lei_no_NT\Textos\HTML"
convert_all_docx_to_html(input_directory, output_directory)
