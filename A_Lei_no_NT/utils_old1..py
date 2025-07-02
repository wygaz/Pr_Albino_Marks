import os
import re
import uuid
from bs4 import BeautifulSoup
from django.utils.text import slugify
from docx import Document
from io import BytesIO
from datetime import datetime
from django.utils.html import strip_tags

from docx import Document
import re

def docx_para_html(arquivo):
    doc = Document(arquivo)
    html = []
    titulo = None
    lista_aberta = []
    atual_indent = None

    def fechar_listas_ate(nivel=0):
        while len(lista_aberta) > nivel:
            html.append(f'</{lista_aberta.pop()}>')

    def detectar_lista_manual(texto):
        # Listas ordenadas: 1., 1.1., 1), a), A.
        if re.match(r'^(\d+[\.\)]|\d+\.\d+[\.\)]?|\(?[a-zA-Z]\))\s+', texto):
            return 'ol'
        # Listas não ordenadas: -, *, •, ·, etc.
        elif re.match(r'^[-*•·+]\s+', texto):
            return 'ul'
        else:
            return None

    for par in doc.paragraphs:
        estilo = par.style.name.lower()
        texto = par.text.strip()
        indent = par.paragraph_format.left_indent
        nivel = int((indent.pt if indent else 0) // 18)

        # Ignorar parágrafos vazios
        if not texto:
            continue

        # Definir título com base no primeiro heading
        if not titulo and estilo.startswith("heading"):
            titulo = texto
            html.append(f'<h2>{texto}</h2>')
            continue

        tipo_lista = detectar_lista_manual(texto)

        if tipo_lista:
            # Remover o marcador da lista
            texto = re.sub(r'^(\(?[a-zA-Z0-9]+\)?[\.\)]?|\d+\.\d+\.?)\s+|^[-*•·+]\s+', '', texto).strip()

            # Abrir novas listas se necessário
            if atual_indent != nivel or (not lista_aberta or lista_aberta[-1] != tipo_lista):
                fechar_listas_ate(nivel)
                html.append(f'<{tipo_lista}>')
                lista_aberta.append(tipo_lista)
                atual_indent = nivel

            html.append(f'<li>{texto}</li>')
        else:
            # Se não for lista, fecha qualquer lista aberta
            fechar_listas_ate()
            atual_indent = None

            if estilo.startswith('heading'):
                html.append(f'<h3>{texto}</h3>')
            elif estilo == 'intense quote':
                html.append(f'<blockquote><strong>{texto}</strong></blockquote>')
            elif estilo == 'quote':
                html.append(f'<blockquote>{texto}</blockquote>')
            elif estilo == 'normal' or estilo == 'body text':
                html.append(f'<p>{texto}</p>')
            else:
                html.append(f'<div>{texto}</div>')

    fechar_listas_ate()
    return '\n'.join(html), titulo or "Sem Título"



#------------------------------------------
# fim da função docx_para_html

def gerar_titulo_numerado(titulo_base, ordem_por='id'):
    from django.apps import apps
    Artigo = apps.get_model('A_Lei_no_NT', 'Artigo')

    # Padrão para identificar numeração no final
    padrao_numerado = re.compile(r' - \d+ de \d+$')

    # Buscar todos os artigos que compartilham o mesmo título base
    artigos_com_titulo_base = Artigo.objects.filter(
        titulo__startswith=titulo_base
    ).order_by(ordem_por)

    # Verifica se o novo artigo já existe (evita duplicação)
    total = artigos_com_titulo_base.count() + 1

    # Remove numeração dos anteriores antes de renumerar
    artigos_limpos = []
    for artigo in artigos_com_titulo_base:
        titulo_sem_num = padrao_numerado.sub('', artigo.titulo).strip()
        artigo.titulo = titulo_sem_num
        artigos_limpos.append(artigo)

    # Renumera os anteriores com base no novo total
    for i, artigo in enumerate(artigos_limpos, start=1):
        artigo.titulo = f"{titulo_base} - {i} de {total}"
        artigo.save()

    # Retorna o título numerado do novo artigo
    return f"{titulo_base} - {total} de {total}"


def gerar_slug(titulo):
    from .models import Artigo  # ✅ Importação local para evitar ciclo

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
