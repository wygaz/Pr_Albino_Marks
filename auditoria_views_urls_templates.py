import os
import re

views_path = 'A_Lei_no_NT/views.py'
urls_path = 'A_Lei_no_NT/urls.py'
templates_path = 'A_Lei_no_NT/Templates/A_Lei_no_NT/'
EXTENSAO_TEMPLATE = '.html'

def extrair_views():
    with open(views_path, 'r', encoding='utf-8') as f:
        return [re.findall(r'def (\w+)\(', linha)[0] for linha in f if linha.strip().startswith('def ')]

def extrair_nomes_urls():
    with open(urls_path, 'r', encoding='utf-8') as f:
        return re.findall(r"name=['\"]([\w_]+)['\"]", f.read())

def listar_templates():
    return [f for f in os.listdir(templates_path) if f.endswith(EXTENSAO_TEMPLATE)]

def padronizar(nome_view):
    if nome_view.startswith('criar') or nome_view.endswith('criar'):
        return 'criar'
    elif nome_view.startswith('editar') or nome_view.endswith('editar') or 'update' in nome_view:
        return 'editar'
    elif nome_view.startswith('visualizar') or 'detalhe' in nome_view:
        return 'visualizar'
    elif nome_view.startswith('listar') or 'list' in nome_view:
        return 'listar'
    elif nome_view.startswith('deletar') or 'delete' in nome_view:
        return 'deletar'
    elif nome_view == 'home':
        return 'home'
    return 'outro'

views = extrair_views()
urls = extrair_nomes_urls()
templates = listar_templates()

with open('relatorio_cruzado_views_urls_templates.txt', 'w', encoding='utf-8') as rel:
    rel.write("📊 RELATÓRIO DE VIEWS, URLs E TEMPLATES\n\n")
    for view in views:
        nome_esperado = f"{view}.html"
        tem_url = '✔' if view in urls else '❌'
        tem_template = '✔' if nome_esperado in templates else '❌'
        encontrado = next((t for t in templates if view in t), 'N/A')
        categoria = padronizar(view)

        rel.write(f"{view:<25} | URL: {tem_url} | TEMPLATE: {tem_template} | Esperado: {nome_esperado:<25} | Encontrado: {encontrado} | Tipo: {categoria}\n")

print("✅ Relatório gerado: relatorio_cruzado_views_urls_templates.txt")
