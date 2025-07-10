import os
import re

# CONFIG
PASTA_VIEWS = 'A_Lei_no_NT/views.py'
PASTA_URLS = 'A_Lei_no_NT/urls.py'
PASTA_TEMPLATES = 'A_Lei_no_NT/Templates/A_Lei_no_NT'
EXTENSAO_TEMPLATE = '.html'

relatorio = []

# Função utilitária para carregar views definidas
def extrair_views():
    with open(PASTA_VIEWS, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    return [re.findall(r'def (\w+)\(', linha)[0] for linha in linhas if linha.strip().startswith('def ')]

# Extrair rotas nomeadas
def extrair_nomes_urls():
    with open(PASTA_URLS, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    return re.findall(r"name=['\"]([\w_]+)['\"]", conteudo)

# Listar templates
def listar_templates():
    return [arq for arq in os.listdir(PASTA_TEMPLATES) if arq.endswith(EXTENSAO_TEMPLATE)]

# Execução
views = extrair_views()
urls = extrair_nomes_urls()
templates = listar_templates()

relatorio.append("📊 AUDITORIA DE NOMES (views, urls, templates)\n")

for view in views:
    nome_base = view.replace('criar_', 'criar').replace('editar_', 'editar')
    template_esperado = view + EXTENSAO_TEMPLATE
    tem_url = view in urls
    tem_template = template_esperado in templates

    status = []
    if tem_url:
        status.append("URL ✔")
    else:
        status.append("URL ❌")

    if tem_template:
        status.append("TEMPLATE ✔")
    else:
        status.append(f"TEMPLATE ❌ (esperado: {template_esperado})")

    simbolo = "✔" if tem_url and tem_template else "⚠️"
    relatorio.append(f"{simbolo} View: {view} → {' | '.join(status)}")

# Salvar relatório
with open('relatorio_auditoria.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(relatorio))

print("✅ Relatório gerado: relatorio_auditoria.txt")
