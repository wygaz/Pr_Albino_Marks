import os
import re
import uuid
import unicodedata
from io import BytesIO
from unidecode import unidecode
from bs4 import BeautifulSoup
from django.utils.text import slugify
from docx import Document
from io import BytesIO
from datetime import datetime
from django.utils.html import strip_tags
from re import split
from docx.text.paragraph import Paragraph
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

import uuid
from unidecode import unidecode
from django.utils.text import slugify

def gerar_slug(titulo):
    from .models import Artigo
    
    if not titulo or not titulo.strip():
        titulo = gerar_titulo_numerado()  # fallback se título for vazio ou só espaços

    slug_base = slugify(unidecode(titulo))
    if not slug_base:
        slug_base = f'artigo-{uuid.uuid4().hex[:6]}'

    slug = slug_base
    contador = 2
    while Artigo.objects.filter(slug=slug).exists():
        slug = f"{slug_base}-{contador}"
        contador += 1
    return slug


import uuid
from unidecode import unidecode
from django.utils.text import slugify

def gerar_slug(titulo):
    from .models import Artigo
    
    if not titulo or not titulo.strip():
        titulo = gerar_titulo_numerado()  # fallback se o título vier vazio

    slug_base = slugify(unidecode(titulo))  # remove acentos e espaços
    if not slug_base:
        slug_base = f'artigo-{uuid.uuid4().hex[:6]}'  # fallback para casos extremos

    slug = slug_base
    contador = 2
    while Artigo.objects.filter(slug=slug).exists():
        slug = f"{slug_base}-{contador}"
        contador += 1
    return slug

def remover_autor_do_conteudo(html, autor):
    from bs4 import BeautifulSoup
    import re

    soup = BeautifulSoup(html, 'html.parser')
    autor_lower = autor.lower().strip()
    candidatos = soup.find_all(['p', 'li'])[:3]  # verifica só os 3 primeiros parágrafos

    for tag in candidatos:
        texto = tag.get_text(strip=True).lower()

        # Remove se contiver nome do autor + poucas palavras
        if autor_lower in texto and len(texto.split()) <= 6:
            tag.decompose()

        # Remove se começar com algo como "1. Albino Marks", "I. Albino Marks", "a) Albino Marks"
        if re.match(r'^(\d+\.|[ivxlc]+\.|[a-z]\))\s*' + re.escape(autor_lower), texto):
            tag.decompose()

    return str(soup)

        
def gerar_titulo_numerado(titulo_base, ordem_por='id'):
    import re
    from django.apps import apps
    Artigo = apps.get_model('A_Lei_no_NT', 'Artigo')

    # Regex para detectar numeração no final do título
    padrao_numerado = re.compile(r' - \d+ de \d+$')

    # Buscar todos os artigos com o mesmo título base
    artigos_com_titulo_base = Artigo.objects.filter(
        titulo__startswith=titulo_base
    ).order_by(ordem_por)

    # Remover a numeração antiga de todos
    artigos_limpos = []
    for artigo in artigos_com_titulo_base:
        artigo.titulo = padrao_numerado.sub('', artigo.titulo).strip()
        artigos_limpos.append(artigo)

    total = len(artigos_limpos) + 1  # Incluindo o novo que será criado

    # Se só existe 1, deixa o título limpo (sem numeração retroativa)
    if total == 1:
        return titulo_base

    # Renumera retroativamente todos os artigos anteriores
    for i, artigo in enumerate(artigos_limpos, start=1):
        artigo.titulo = f"{titulo_base} - {i} de {total}"
        artigo.save()

    # Retorna o título do novo artigo
    return f"{titulo_base} - {total} de {total}"


def detectar_titulo_possivel(paragrafos):
    for p in paragrafos[:5]:
        texto = ''.join(run.text for run in p.runs).strip()
        if texto and len(texto.split()) <= 12 and p.style.name.lower().startswith('heading'):
            return texto
    for p in paragrafos[:5]:
        texto = ''.join(run.text for run in p.runs).strip()
        if texto and len(texto.split()) <= 12 and p.alignment in [1, 2]:
            return texto
    for p in paragrafos[:5]:
        texto = ''.join(run.text for run in p.runs).strip()
        if texto and len(texto.split()) <= 12:
            return texto
    return None

def detectar_autor(paragrafos):
    for i, p in enumerate(paragrafos[1:4], start=1):
        texto = ''.join(run.text for run in p.runs).strip()
        if not texto or len(texto) > 100:
            continue
        if i in (1, 2) and len(texto.split()) <= 5 and len(p.runs) <= 3:
            return texto
        if p.alignment == WD_PARAGRAPH_ALIGNMENT.RIGHT:
            return texto
    return None

def remover_autor_do_conteudo(html, autor):
    if not autor:
        return html

    soup = BeautifulSoup(html, 'html.parser')
    for p in soup.find_all('p'):
        if autor in p.text.strip():
            p.decompose()
            break  # Remove apenas a primeira ocorrência do nome do autor
    html_final = str(soup)

    html_final = converter_subtitulos_manualmente_numerados(html_final)

    return html_final

def formatar_paragrafo(paragrafo):
    partes = []

    for run in paragrafo.runs:
        texto = run.text.replace('\n', '')  # removendo quebras de linha
        if not texto.strip():
            continue

        estilo = ''
        if run.bold:
            estilo += 'font-weight:bold;'
        if run.italic:
            estilo += 'font-style:italic;'
        if run.underline:
            estilo += 'text-decoration:underline;'

        if estilo:
            partes.append(f'<span style="{estilo}">{texto}</span>')
        else:
            partes.append(texto)

    return ''.join(partes)

def converter_para_html(paragrafos):
    html = ''
    padrao_lista = re.compile(r'^(\d+\.)|([ivxlc]+\.)|([IVXLC]+\.)|([a-zA-Z]\.)|([a-zA-Z]\))\s+')
    for p in paragrafos:
        texto_bruto = ''.join(run.text for run in p.runs).strip()
        if not texto_bruto:
            continue
        texto_formatado = formatar_paragrafo(p)
        if p.style.name.lower().startswith('heading'):
            html += f'<h2>{texto_formatado}</h2>\n'
        elif padrao_lista.match(texto_bruto):
            # Remove o prefixo manual antes de inserir como item de lista
            texto_formatado = padrao_lista.sub('', texto_formatado).strip()
            html += f'<ol><li>{texto_formatado}</li></ol>\n'
        elif texto_bruto.startswith(('-', '*', '•')):
            html += f'<ul><li>{texto_formatado[1:].strip()}</li></ul>\n'
        else:
            html += f'<p>{texto_formatado}</p>\n'
    return html

def renomear_com_slug(caminho_arquivo, slug):
    ext = os.path.splitext(caminho_arquivo)[1]
    return f"{slug}{ext}"


def renomear_arquivo_word(arquivo):
    nome_base = os.path.basename(arquivo.name)
    novo_nome = gerar_slug(nome_base.replace('.docx', '')) + '.docx'
    return novo_nome

def renomear_imagem_capa(nome_original):
    nome_base, ext = os.path.splitext(nome_original)
    nome_slug = gerar_slug(nome_base)
    return nome_slug + ext

def converter_subtitulos_manualmente_numerados(html):
    padrao = r'<p>\s*(?P<numero>\d+)[\.\-–)]\s+(?P<texto>.*?)</p>'

    def substituir(match):
        numero = match.group("numero")
        texto = match.group("texto").strip()
        resultado = f'<h2>{numero}. <strong>{texto}</strong></h2>'
        print(f'🔎 número: {numero}')
        print(f'🔎 texto: {texto}')
        print(f'✅ resultado: {resultado}\n')
        return resultado

    return re.sub(padrao, substituir, html)

def converter_para_html(paragrafos):
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    html = ""
    lista_aberta = False
    tipo_lista = None
    contador_ord = 0
    contador_nao_ord = 0

    def fecha_lista():
        nonlocal html, lista_aberta, tipo_lista
        if lista_aberta:
            html += f'</{tipo_lista}>\n'
            lista_aberta = False
            tipo_lista = None

    def detectar_item_manual(texto):
        import re
        if re.match(r"^\s*[\-\u2022\*]\s+", texto):  # - • *
            return "ul"
        if re.match(r"^\s*(\d+|[a-zA-Z]+)[\.\)\-–]\s+", texto):  # 1. a) I) A. etc
            return "ol"
        return None

    def eh_titulo_exemplo(texto):
        import re
        return bool(re.match(r"^\d+\.\s+Lista", texto.strip(), re.IGNORECASE))

    for p in paragrafos:
        texto_corrigido = ''.join(run.text for run in p.runs).strip()
        alinhado_central = p.alignment == WD_ALIGN_PARAGRAPH.CENTER
        estilo = p.style.name.lower()

        if not texto_corrigido:
            fecha_lista()
            html += "<br>\n"
            continue

        # 🛑 Ignora título de exemplo de lista (ex: "1. Lista Não Ordenada")
        if eh_titulo_exemplo(texto_corrigido):
            fecha_lista()
            html += f"<p><strong>{texto_corrigido}</strong></p>\n"
            continue

        tipo_item = detectar_item_manual(texto_corrigido)

        # ▶️ Item de lista
        if tipo_item:
            if not lista_aberta or tipo_lista != tipo_item:
                fecha_lista()
                html += f"<{tipo_item}>\n"
                lista_aberta = True
                tipo_lista = tipo_item
            item = texto_corrigido.split(' ', 1)[1] if ' ' in texto_corrigido else texto_corrigido
            html += f"<li>{item}</li>\n"
        else:
            fecha_lista()
            # 🔤 Tratamento de formatação inline
            partes = []
            for run in p.runs:
                t = run.text.replace('\n', '<br>').strip()
                if not t:
                    continue
                if run.bold:
                    t = f"<strong>{t}</strong>"
                if run.italic:
                    t = f"<em>{t}</em>"
                if run.underline:
                    t = f"<u>{t}</u>"
                partes.append(t)
            linha_formatada = ' '.join(partes)
            if alinhado_central:
                html += f"<p style='text-align: center'>{linha_formatada}</p>\n"
            else:
                html += f"<p>{linha_formatada}</p>\n"

    fecha_lista()
    return html

def aplicar_estrutura_listas(html):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')

    novas_tags = []
    lista_atual = []
    tipo_lista = None

    print("\n🔍 INICIANDO AGRUPAMENTO DE LISTAS...")

    for i, el in enumerate(soup.contents):
        print(f"\n📄 Elemento {i}: {el.name} — {str(el)[:60]}...")

        if el.name in ['ul', 'ol']:
            itens = el.find_all('li')
            print(f"  ➕ Detectado: lista <{el.name}> com {len(itens)} itens")

            if not itens:
                print("  ⚠️ Lista ignorada (sem itens <li>)")
                continue

            if tipo_lista == el.name:
                lista_atual.extend(itens)
                print(f"  🔁 Continuando lista do tipo <{el.name}> com +{len(itens)} itens")
            else:
                if lista_atual:
                    nova_lista = soup.new_tag(tipo_lista)
                    for item in lista_atual:
                        nova_lista.append(item)
                    novas_tags.append(nova_lista)
                    print(f"  ✅ Lista <{tipo_lista}> finalizada e adicionada com {len(lista_atual)} itens")

                tipo_lista = el.name
                lista_atual = itens
                print(f"  🔄 Nova lista <{el.name}> iniciada")
        else:
            if lista_atual:
                nova_lista = soup.new_tag(tipo_lista)
                for item in lista_atual:
                    nova_lista.append(item)
                novas_tags.append(nova_lista)
                print(f"  ✅ Lista <{tipo_lista}> finalizada e adicionada com {len(lista_atual)} itens")

                lista_atual = []
                tipo_lista = None

            novas_tags.append(el)
            print(f"  📌 Elemento não-lista adicionado normalmente: <{el.name}>")

    if lista_atual:
        nova_lista = soup.new_tag(tipo_lista)
        for item in lista_atual:
            nova_lista.append(item)
        novas_tags.append(nova_lista)
        print(f"  ✅ Lista <{tipo_lista}> finalizada no final com {len(lista_atual)} itens")

    print("🏁 AGRUPAMENTO DE LISTAS FINALIZADO.\n")
    return str(BeautifulSoup(''.join(str(tag) for tag in novas_tags), 'html.parser'))


def docx_para_html(arquivo):
    from docx import Document
    from bs4 import BeautifulSoup
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document(arquivo)
    paragrafos = doc.paragraphs

    # 🔍 Detectar título (máx. 12 palavras, estilo Heading, ou centralizado em negrito)
    titulo = None
    indice_titulo = None
    for i, p in enumerate(paragrafos[:5]):
        texto = ''.join(run.text for run in p.runs).strip()
        if texto and len(texto.split()) <= 12 and (p.style.name.startswith('Heading') or p.runs[0].bold or p.alignment == WD_ALIGN_PARAGRAPH.CENTER):
            titulo = texto
            indice_titulo = i
            break

    # 🔐 Cópia segura dos parágrafos, sem o título
    paragrafos_sem_titulo = [p for i, p in enumerate(paragrafos) if i != indice_titulo]

    # 🎯 Detectar autor com base no conteúdo restante
    autor = detectar_autor(paragrafos_sem_titulo)

    # 🧾 Converter parágrafos em HTML (com quebra de linha, negrito, itálico etc.)
    html = converter_para_html(paragrafos_sem_titulo)

    # 📋 Adicionar tabelas do documento
    for tabela in doc.tables:
        html += '<table border="1" style="border-collapse: collapse; margin-top: 1em;">'
        for linha in tabela.rows:
            html += '<tr>'
            for celula in linha.cells:
                conteudo = '<br>'.join(p.text for p in celula.paragraphs)
                html += f'<td style="padding: 4px;">{conteudo}</td>'
            html += '</tr>'
        html += '</table>'

    # 🧼 Remover nome do autor do conteúdo renderizado
    html = remover_autor_do_conteudo(html, autor)

    # 🧠 Agrupamento de listas sequenciais (ul, ol)
    soup = BeautifulSoup(html, 'html.parser')
    novas_tags = []
    lista_atual = []
    tipo_lista = None

    for el in soup.contents:
        if el.name in ['ul', 'ol']:
            if tipo_lista == el.name:
                lista_atual.extend(el.find_all('li'))
            else:
                if lista_atual:
                    nova_lista = soup.new_tag(tipo_lista)
                    for item in lista_atual:
                        nova_lista.append(item)
                    novas_tags.append(nova_lista)
                tipo_lista = el.name
                lista_atual = el.find_all('li')
        else:
            if lista_atual:
                nova_lista = soup.new_tag(tipo_lista)
                for item in lista_atual:
                    nova_lista.append(item)
                novas_tags.append(nova_lista)
                lista_atual = []
                tipo_lista = None
            novas_tags.append(el)

    if lista_atual:
        nova_lista = soup.new_tag(tipo_lista)
        for item in lista_atual:
            nova_lista.append(item)
        novas_tags.append(nova_lista)

    soup.clear()
    for tag in novas_tags:
        soup.append(tag)

    # 🔧 Converte para string e aplica estrutura inteligente de listas e subtítulos
    try:
        html_final = str(soup)
        html_final = aplicar_estrutura_listas(html_final)
    except Exception as e:
        print("⚠️ Erro ao processar HTML final:", e)
        html_final = ""

    # ✅ Retorna conteúdo final + título extraído + autor identificado
    print("Retornando:", html_final, titulo)
    return html_final, titulo, autor
