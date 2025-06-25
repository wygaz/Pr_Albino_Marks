import os
import shutil

templates_dir = "A_Lei_no_NT/Templates/A_Lei_no_NT/"
backup_dir = "A_Lei_no_NT/Back_Templates/"
os.makedirs(backup_dir, exist_ok=True)

renomeacoes = {
    "artigo_lista.html": "lista_artigos.html",
    "artigo_visualizar.html": "visualizar_artigo.html",
    "artigo_form.html": "criar_artigo.html"
}

for antigo, novo in renomeacoes.items():
    caminho_antigo = os.path.join(templates_dir, antigo)
    caminho_novo = os.path.join(templates_dir, novo)
    caminho_backup = os.path.join(backup_dir, antigo)

    if os.path.exists(caminho_antigo):
        shutil.copy2(caminho_antigo, caminho_backup)
        os.rename(caminho_antigo, caminho_novo)
        print(f"✅ {antigo} → {novo} (backup salvo)")
    else:
        print(f"⚠️ Arquivo não encontrado: {antigo}")
