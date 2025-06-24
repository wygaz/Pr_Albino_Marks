import os
import unicodedata
import re

# Lista de títulos dos artigos (na mesma ordem das imagens 1.jpg, 2.jpg...)
titulos = [
    "O Conflito Cósmico e os Dois Poderes em Confronto",
    "As Predições do Profeta João no Apocalipse",
    "O Sétimo Selo",
    "As Sete Trombetas e os Sete Últimos Flagelos",
    "O Dilúvio",
    "A Justiça de Deus e a Justiça dos Fariseus",
    "Ninguém é Justificado por Obras da Lei",
    "O Eterno Plano da Redenção",
    "O grande conflito e o plano da salvação",
    "Guerra de Conceitos Espirituais no Céu",
    "Os Escritores do Novo Testamento e a Lei",
    "O Apóstolo Paulo e a Lei",
    "O Novo Testamento, Jesus, a Lei e os Profetas",
    "Jesus e a Lei (nómos)",
    "Jesus, não revogou, mas magnificou a Lei"
]

# Caminho da pasta onde estão as imagens numeradas
caminho_imagens = r"C:\Users\Wanderley\Apps\PR_ALBINO_MARKS\A_Lei_no_NT\static\imagens"

# Função para gerar o slug igual ao Django
def slugify(value):
    value = str(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "_", value)

# Renomeia as imagens da pasta com base nos slugs
for i, titulo in enumerate(titulos, start=1):
    slug = slugify(titulo)
    nome_atual = os.path.join(caminho_imagens, f"{i}.jpg")
    nome_novo = os.path.join(caminho_imagens, f"{slug}.jpg")
    
    if os.path.exists(nome_atual):
        os.rename(nome_atual, nome_novo)
        print(f"Renomeado: {nome_atual} -> {nome_novo}")
    else:
        print(f"Imagem não encontrada: {nome_atual}")
