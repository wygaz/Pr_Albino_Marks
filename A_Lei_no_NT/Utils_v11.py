
# utils.py - versão v11

def verificar_se_e_autor(paragrafo, nomes_autores_bd):
    # Junta todo o texto do parágrafo (runs)
    texto_completo = ''.join([run.text.strip() for run in paragrafo.runs if run.text.strip()])
    if not texto_completo:
        return False

    # Verifica se começa com "Autor:"
    if texto_completo.startswith("Autor:"):
        return True

    # Verifica alinhamento à direita (estilo ou elemento específico)
    alinhado_direita = (paragrafo.alignment == 2)  # 2 é alinhamento à direita em python-docx

    # Verifica se o texto está presente na base de dados de autores
    for nome in nomes_autores_bd:
        if nome.lower() in texto_completo.lower():
            return True if alinhado_direita else False

    return False
