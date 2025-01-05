import os

# Caminho do diretório 'staticfiles'
staticfiles_dir = r'C:\Users\Wanderley\Apps\Pr_Albino_Marks\staticfiles'

# Criar um conjunto para rastrear os arquivos únicos
arquivos_unicos = set()

# Percorrer todos os arquivos no diretório 'staticfiles'
for root, dirs, files in os.walk(staticfiles_dir):
    for file in files:
        caminho_absoluto = os.path.join(root, file)
        caminho_relativo = os.path.relpath(caminho_absoluto, staticfiles_dir)

        if caminho_relativo in arquivos_unicos:
            # Se o arquivo já foi encontrado, removê-lo
            print(f"Removendo duplicata: {caminho_absoluto}")
            os.remove(caminho_absoluto)
        else:
            # Caso contrário, adicioná-lo ao conjunto de únicos
            arquivos_unicos.add(caminho_relativo)

print("Processo concluído.")
