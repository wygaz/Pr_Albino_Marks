import os
import re
import uuid
from bs4 import BeautifulSoup
from django.utils.text import slugify
from docx import Document
from io import BytesIO
from datetime import datetime
from django.utils.html import strip_tags
from re import split
from unidecode import unidecode
from docx.text.paragraph import Paragraph

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

def docx_para_html(arquivo):
    document = Document(arquivo)
    soup = BeautifulSoup("", "html.parser")
    titulo_extraido = None
    possiveis_autores = []
    novos_elementos = []
    buffer_paragrafo = None

    autores_cadastrados = [
        "Pr. Albino Marks", "Albino Marks", "Albino M.", "Pr. A. Marks"
    ]

    def limpar_texto_runs(paragrafo):
        return "".join([r.text.strip() for r in paragrafo.runs]).strip()

    def formatar_runs(paragrafo):
        partes = []
        for run in paragrafo.runs:
            texto = run.text.replace("\xa0", " ")
            if not texto:
                continue
            if run.bold:
                texto = f"<strong>{texto}</strong>"
            if run.italic:
                texto = f"<em>{texto}</em>"
            if run.underline:
                texto = f"<u>{texto}</u>"
            partes.append(texto)
        return " ".join(partes).strip()

    for i, paragrafo in enumerate(document.paragraphs):
        texto = limpar_texto_runs(paragrafo)
        if not texto:
            continue

        alinhamento = getattr(paragrafo.paragraph_format.alignment, "name", "").lower()

        if not titulo_extraido:
            fonte_maior = any(r.font.size and r.font.size.pt > 12 for r in paragrafo.runs)
            if fonte_maior:
                titulo_extraido = texto
                continue

        if i in (1, 2):
            if alinhamento == "right" or len(texto) <= 100:
                if any(autor in texto for autor in autores_cadastrados):
                    possiveis_autores.append(texto)
                    continue

        texto_formatado = formatar_runs(paragrafo)
        p_tag = soup.new_tag("p")
        p_tag.append(BeautifulSoup(texto_formatado, "html.parser"))
        novos_elementos.append(p_tag)

    if not titulo_extraido:
        titulo_extraido = "Artigo sem Título"

    soup.clear()
    for tag in novos_elementos:
        soup.append(tag)

    return str(soup), titulo_extraido



#============================ Final da docx_para_html()=============================


def gerar_titulo_numerado(titulo_base, ordem_por='id'):
    from django.apps import apps
    Artigo = apps.get_model('A_Lei_no_NT', 'Artigo')

    padrao_numerado = re.compile(r' - \d+ de \d+$')
    artigos_com_titulo_base = Artigo.objects.filter(titulo__startswith=titulo_base).order_by(ordem_por)
    total = artigos_com_titulo_base.count() + 1

    artigos_limpos = []
    for artigo in artigos_com_titulo_base:
        titulo_sem_num = padrao_numerado.sub('', artigo.titulo).strip()
        artigo.titulo = titulo_sem_num
        artigos_limpos.append(artigo)

    for i, artigo in enumerate(artigos_limpos, start=1):
        artigo.titulo = f"{titulo_base} - {i} de {total}"
        artigo.save()

    return f"{titulo_base} - {total} de {total}"

def gerar_slug(titulo):
    from .models import Artigo
    base_slug = slugify(titulo)
    slug = base_slug
    contador = 1
    while Artigo.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{contador}"
        contador += 1
    return slug

def renomear_imagem_capa(instance, filename):
    base, ext = os.path.splitext(filename)
    nome_base = slugify(instance.slug or instance.titulo or uuid.uuid4().hex[:8])
    novo_nome = f"{nome_base}-capa{ext.lower()}"
    return os.path.join('capas', novo_nome)

def renomear_arquivo_word(instance, filename):
    base, ext = os.path.splitext(filename)
    nome_base = slugify(instance.slug or instance.titulo or uuid.uuid4().hex[:10])
    novo_nome = f"{nome_base}{ext.lower()}"
    return os.path.join('uploads', novo_nome)
