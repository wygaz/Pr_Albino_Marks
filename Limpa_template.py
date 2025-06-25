import os

PASTA_TEMPLATES = 'A_Lei_no_NT/Templates'
EXTENSAO = '.html'
padroes_suspeitos = ['old', 'copy', 'test', 'backup', 'temp', 'versao', 'v0', 'v1', 'anterior']

arquivos_suspeitos = []

for raiz, _, arquivos in os.walk(PASTA_TEMPLATES):
    for nome in arquivos:
        if nome.endswith(EXTENSAO):
            nome_lower = nome.lower()
            if any(p in nome_lower for p in padroes_suspeitos):
                arquivos_suspeitos.append(os.path.join(raiz, nome))

with open('relatorio_limpeza_templates.txt', 'w', encoding='utf-8') as f:
    f.write("📁 Arquivos suspeitos no diretório de Templates:\n\n")
    for caminho in arquivos_suspeitos:
        f.write(f"{caminho}\n")

print("✅ Relatório gerado: relatorio_limpeza_templates.txt")
