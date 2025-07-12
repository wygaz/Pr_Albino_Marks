import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# Caminhos base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
PDF_DIR = os.path.join(BASE_DIR, 'media', 'pdfs')

# Garantir que pasta exista
os.makedirs(PDF_DIR, exist_ok=True)

# Inicializa Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template('modelo_artigo_pdf.html')

# Exemplo de artigo
artigos = [
    {
        'slug': 'a-justica-de-deus',
        'titulo': 'A Justiça de Deus',
        'conteudo': """
            <p>Este é o conteúdo formatado em HTML do artigo. Pode conter <strong>negrito</strong>, <em>itálico</em> e até listas:</p>
            <ul><li>Item 1</li><li>Item 2</li></ul>
        """
    },
    # Você pode incluir outros artigos na lista
]

# Geração de PDFs
for artigo in artigos:
    html_renderizado = template.render(
        titulo=artigo['titulo'],
        conteudo=artigo['conteudo']
    )

    caminho_saida = os.path.join(PDF_DIR, f"{artigo['slug']}.pdf")
    HTML(string=html_renderizado).write_pdf(caminho_saida)
    print(f"✅ PDF gerado: {caminho_saida}")
