import os, re, shutil
import unicodedata
from io import BytesIO
from unidecode import unidecode
from bs4 import BeautifulSoup
from django.utils.text import slugify
from uuid import uuid4
from docx import Document
from io import BytesIO
from datetime import datetime
from django.utils.html import strip_tags
from re import split
from docx.text.paragraph import Paragraph
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from django.db import transaction
from django.apps import apps
from pathlib import Path
from django.conf import settings

# utils.py (trecho necessário para o auditor)

# Padrões de numeração que queremos remover do fim do título
_PADROES_NUM = [
    r"\s*-\s*\d+\s+de\s+\d+\s*$",
    r"\s*\(\s*\d+\s*/\s*\d+\s*\)\s*$",
    r"\s*n[ºo]\.?\s*\d+\s*$",
    r"\s*-\s*parte\s*\d+\s*$",
]


def path_docx_por_slug(slug: str) -> Path:
    return Path(settings.MEDIA_ROOT) / "uploads" / f"{slug}.docx"

def localizar_docx(slug: str) -> Path | None:
    """
    Procura DOCX no padrão novo e nos legados:
      uploads/<slug>.docx
      uploads/artigo_<slug>*.docx
      (se slug == '<base>-k-de-N') tenta também: uploads/artigo_<base>-k-de-*.docx
      uploads/artigo_temp_*.docx (fallback)
    """
    uploads = Path(settings.MEDIA_ROOT) / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)

    alvo = uploads / f"{slug}.docx"
    if alvo.exists():
        return alvo

    legados = sorted(uploads.glob(f"artigo_{slug}*.docx"))
    if legados:
        return max(legados, key=lambda p: p.stat().st_mtime)

    m = re.match(r"^(?P<base>.+)-(?P<k>\d+)-de-(?P<n>\d+)$", slug)
    if m:
        base = m.group("base")
        k = m.group("k")
        flex = sorted(uploads.glob(f"artigo_{base}-{k}-de-*.docx"))
        if flex:
            return max(flex, key=lambda p: p.stat().st_mtime)

    temps = sorted(uploads.glob("artigo_temp_*.docx"))
    if temps:
        return max(temps, key=lambda p: p.stat().st_mtime)

    return None

def normalizar_docx_para_padrao(slug: str, origem: Path) -> Path:
    """Move/renomeia para uploads/<slug>.docx (overwrite seguro)."""
    destino = path_docx_por_slug(slug)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if origem != destino:
        destino.unlink(missing_ok=True)           # overwrite seguro
        shutil.move(origem.as_posix(), destino.as_posix())
    return destino

def encontrar_capa_existente(slug: str) -> Path | None:
    """Retorna a capa existente para um slug (qualquer extensão conhecida)."""
    base = Path(settings.MEDIA_ROOT) / "imagens" / "artigos"
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = base / f"{slug}{ext}"
        if p.exists():
            return p
    # tenta variações 'temp_' geradas em uploads
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        temp = base / f"temp_{slug}{ext}"
        if temp.exists():
            return temp
    return None

def limpar_numeracao(titulo: str) -> str:
    """
    Remove qualquer marcação de numeração no final do título e devolve o 'título-base'.
    """
    base = (titulo or "").strip()
    for pat in _PADROES_NUM:
        base = re.sub(pat, "", base, flags=re.IGNORECASE).strip()
    return base

def path_capa_por_slug(slug: str, ext=".jpg") -> Path:
    return Path(settings.MEDIA_ROOT) / "imagens" / "artigos" / f"{slug}{ext}"


def gerar_slug(titulo):
    from .models import Artigo

    if not titulo or not titulo.strip():
        titulo = "Artigo Sem Título"

    slug_base = slugify(unidecode(titulo))
    if not slug_base:
        slug_base = f"artigo-{uuid4().hex[:6]}"

    slug = slug_base
    contador = 2
    while Artigo.objects.filter(slug=slug).exists():
        slug = f"{slug_base}-{contador}"
        contador += 1

    return slug


