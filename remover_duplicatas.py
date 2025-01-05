import os
import filecmp

# Diretórios
diretorio_pai = r'C:\Users\Wanderley\Apps\Pr_Albino_Marks\A_Lei_no_NT\static\A_Lei_no_NT\imagens'
subdiretorio = os.path.join(diretorio_pai, 'Escolanoar')

# Listar arquivos em ambos os diretórios
arquivos_pai = {arq for arq in os.listdir(diretorio_pai) if os.path.isfile(os.path.join(diretorio_pai, arq))}
arquivos_sub = {arq for arq in os.listdir(subdiretorio) if os.path.isfile(os.path.join(subdiretorio, arq))}

# Verificar duplicatas
duplicados = arquivos_pai.intersection(arquivos_sub)

# Apagar arquivos duplicados do subdiretório
for arquivo in duplicados:
    caminho_arquivo = os.path.join(subdiretorio, arquivo)
    print(f'Removendo: {caminho_arquivo}')
    os.remove(caminho_arquivo)

print('Processo concluído.')
