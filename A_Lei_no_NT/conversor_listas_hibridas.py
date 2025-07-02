
import re
from bs4 import BeautifulSoup

# Define os estilos de simbologia por nível
ESTILOS_HIBRIDOS = {
    0: lambda idx: f"{idx + 1}.",                      # 1., 2., 3.
    1: lambda idx: f"{chr(97 + idx)}.",                # a., b., c.
    2: lambda idx: f"{chr(65 + idx)}.",                # A., B., C.
    3: lambda idx: f"{idx + 1}a.",                     # 1a., 2a., 3a.
    4: lambda idx: f"{chr(97 + idx)}{idx + 1}.",       # a1., b2., etc.
}

def gerar_html_lista_aninhada(lista, nivel=0):
    """
    Recebe uma lista de listas (estrutura de árvore) e retorna o HTML formatado com simbologia híbrida.
    """
    html = "<ul style='list-style-type: none; margin-left: {}px;'>\n".format(20 * nivel)
    for idx, item in enumerate(lista):
        if isinstance(item, str):
            marcador = ESTILOS_HIBRIDOS.get(nivel, lambda i: f"{i + 1}.")(idx)
            html += f"<li><strong>{marcador}</strong> {item}</li>\n"
        elif isinstance(item, list):
            html += gerar_html_lista_aninhada(item, nivel + 1)
    html += "</ul>\n"
    return html

# Exemplo de uso:
if __name__ == "__main__":
    exemplo = [
        "Primeiro item",
        [
            "Subitem 1",
            "Subitem 2"
        ],
        "Segundo item",
        [
            "Subitem 2.1",
            [
                "Sub-subitem a",
                "Sub-subitem b"
            ]
        ]
    ]
    resultado = gerar_html_lista_aninhada(exemplo)
    from pathlib import Path
    Path("listas_hibridas_exemplo.html").write_text(resultado, encoding="utf-8")
    print("Arquivo 'listas_hibridas_exemplo.html' gerado com sucesso.")
