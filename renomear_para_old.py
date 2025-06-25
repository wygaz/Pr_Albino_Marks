import os

# Caminho para o diretório de templates antigos
diretorio = 'templates_deposito'

# Verifica se o diretório existe
if not os.path.isdir(diretorio):
    print(f"❌ Diretório não encontrado: {diretorio}")
else:
    arquivos = os.listdir(diretorio)
    renomeados = []

    for nome_arquivo in arquivos:
        caminho_antigo = os.path.join(diretorio, nome_arquivo)

        # Ignora subdiretórios
        if not os.path.isfile(caminho_antigo):
            continue

        nome, extensao = os.path.splitext(nome_arquivo)
        novo_nome = f"{nome}_old{extensao}"
        caminho_novo = os.path.join(diretorio, novo_nome)

        os.rename(caminho_antigo, caminho_novo)
        renomeados.append((nome_arquivo, novo_nome))

    # Resultado
    print("✅ Arquivos renomeados:")
    for antigo, novo in renomeados:
        print(f"  - {antigo} → {novo}")
