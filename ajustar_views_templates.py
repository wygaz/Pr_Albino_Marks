import os
import shutil

views_path = "A_Lei_no_NT/views.py"
backup_path = views_path + ".bak"

substituicoes = {
    "artigo_lista.html": "lista_artigos.html",
    "artigo_visualizar.html": "visualizar_artigo.html",
    "artigo_form.html": "criar_artigo.html"
}

# Backup
shutil.copy2(views_path, backup_path)

# Leitura e substituição
with open(views_path, "r", encoding="utf-8") as f:
    conteudo = f.read()

alteracoes = []
for antigo, novo in substituicoes.items():
    if antigo in conteudo:
        conteudo = conteudo.replace(antigo, novo)
        alteracoes.append((antigo, novo))

with open(views_path, "w", encoding="utf-8") as f:
    f.write(conteudo)

# Exibir resultado no terminal
if alteracoes:
    print("✅ Substituições realizadas:")
    for antigo, novo in alteracoes:
        print(f"  - {antigo} → {novo}")
    print(f"\n📦 Backup salvo como: {backup_path}")
else:
    print("ℹ️ Nenhuma ocorrência encontrada para substituir.")
