from collections import OrderedDict
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils.html import strip_tags
from django.utils.text import slugify
import re

from A_Lei_no_NT.access import usuario_habilitado_required
from A_Lei_no_NT.models import Artigo
from A_Lei_no_NT.utils_storage import open_file

from .models import Sermao


ARQUIVOS_SERMAO = {
    "pdf-tablet": ("pdf_tablet", "PDF Tablet"),
    "pdf-a4": ("pdf_a4", "PDF A4"),
    "pdf-a5": ("pdf_a5", "PDF A5"),
    "docx-a4": ("docx_a4", "DOCX A4"),
    "relatorio-tecnico": ("relatorio_tecnico_pdf", "Estudo"),
}


def _series_index(sermoes):
    grupos = OrderedDict()
    for sermao in sermoes:
        artigo = getattr(sermao, "artigo_relacionado", None)
        chave = _serie_canonica_sermao(sermao, artigo)
        grupos.setdefault(chave, []).append(sermao)
    return grupos


def _series_anchor(serie: str) -> str:
    return slugify((serie or "sem-serie").strip()) or "sem-serie"


def _formatos_disponiveis(sermao):
    return {
        "tablet": bool(getattr(sermao.pdf_tablet, "name", "")),
        "a4": bool(getattr(sermao.pdf_a4, "name", "")),
        "a5": bool(getattr(sermao.pdf_a5, "name", "")),
        "docx": bool(getattr(sermao.docx_a4, "name", "")),
        "relatorio": bool(getattr(sermao.relatorio_tecnico_pdf, "name", "")),
    }


def _buscar_artigo_relacionado(sermao):
    slug = (sermao.slug or "").strip()
    titulo = (sermao.titulo or "").strip()
    artigo = None
    if slug:
        artigo = Artigo.objects.filter(slug=slug, visivel=True).select_related("area", "autor").first()
    if artigo is None and titulo:
        artigo = Artigo.objects.filter(titulo__iexact=titulo, visivel=True).select_related("area", "autor").first()
    return artigo


def _titulo_canonico_sermao(sermao, artigo=None):
    artigo = artigo or _buscar_artigo_relacionado(sermao)
    return _titulo_exibicao_artigo(artigo) if artigo is not None else (sermao.titulo or "").strip()



_SERIES_GENERICAS = {"series", "serie", "sem serie", "sem-serie", "sem série", ""}


def _serie_canonica_sermao(sermao, artigo=None):
    artigo = artigo or _buscar_artigo_relacionado(sermao)
    serie = (getattr(sermao, "serie", "") or "").strip()
    serie_key = slugify(serie)
    if artigo is not None and getattr(artigo, "area", None):
        area_nome = (artigo.area.nome or "").strip()
        if area_nome and (not serie or serie_key in _SERIES_GENERICAS):
            return area_nome
    return serie or "Sem série"


def _titulo_exibicao_artigo(artigo):
    if artigo is None:
        return ""
    conteudo = getattr(artigo, "conteudo_html", "") or ""
    for tag in ("h1", "h2"):
        m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", conteudo, flags=re.IGNORECASE | re.DOTALL)
        if m:
            titulo = strip_tags(m.group(1)).strip()
            if titulo:
                return titulo
    return (getattr(artigo, "titulo", "") or "").strip()


def _enriquecer_sermao(sermao, artigo=None):
    artigo = artigo or _buscar_artigo_relacionado(sermao)
    sermao.titulo_exibicao = _titulo_canonico_sermao(sermao, artigo)
    sermao.artigo_relacionado = artigo
    sermao.tem_dossie = bool(getattr(sermao.relatorio_tecnico_pdf, "name", ""))
    sermao.serie_canonica = _serie_canonica_sermao(sermao, artigo)
    return sermao


def _resumo_editorial_valido(texto: str, *evitar: str) -> str:
    resumo = (texto or "").strip()
    if not resumo:
        return ""
    resumo_normalizado = " ".join(resumo.lower().split())
    if resumo_normalizado.startswith(("teste ", "teste comparativo", "comparativo ", "rascunho ", "temporario ", "provisorio ")):
        return ""
    for item in evitar:
        alvo = " ".join((item or "").strip().lower().split())
        if alvo and resumo_normalizado == alvo:
            return ""
    return resumo


def _imagem_editorial(sermao=None, artigo=None):
    for obj in (sermao, artigo):
        field = getattr(obj, "imagem_capa", None)
        if field and getattr(field, "name", ""):
            return field
    return None


def _conteudo_html_dossie(sermao):
    field_name = getattr(getattr(sermao, "relatorio_tecnico_pdf", None), "name", "") or ""
    if not field_name:
        return ""
    basename = Path(field_name).name
    html_name = Path(basename).with_suffix(".html").name
    dossies_dir = Path(settings.BASE_DIR) / "Apenas_Local" / "operacional" / "dossies" / "formatados"
    html_path = dossies_dir / html_name
    if not html_path.exists():
        candidatos = []
        if getattr(sermao, "ordem", 0):
            candidatos.extend(sorted(dossies_dir.glob(f"{int(sermao.ordem):02d}__*__dossie__a4.html")))
        slug_alvo = slugify((getattr(sermao, "titulo", "") or "").strip())
        if slug_alvo:
            candidatos.extend(sorted(dossies_dir.glob(f"*{slug_alvo}*__dossie__a4.html")))
        if candidatos:
            html_path = candidatos[0]
        else:
            return ""
    try:
        html = html_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    if any(marca in html for marca in ("Ã", "â€", "â€“", "â€”", "Â")):
        try:
            html = html.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    main_match = re.search(
        r"<main\b[^>]*class=[\"'][^\"']*\breading-surface\b[^\"']*[\"'][^>]*>(.*?)</main>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if main_match:
        return main_match.group(1).strip()
    lower_html = html.lower()
    body_start = lower_html.find("<body")
    if body_start >= 0:
        body_tag_end = html.find(">", body_start)
        body_end = lower_html.rfind("</body>")
        if body_tag_end >= 0 and body_end > body_tag_end:
            return html[body_tag_end + 1:body_end].strip()
    return html.strip()


def _normalizar_mojibake(html: str) -> str:
    if not html:
        return ""
    if any(marca in html for marca in ("Ã", "â€", "â€“", "â€”", "Â")):
        try:
            return html.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return html
    return html


def _extract_html_fragment(html: str, class_name: str) -> str:
    if not html:
        return ""
    pattern = rf'''<(?P<tag>\w+)\b[^>]*class=["'][^"']*\b{re.escape(class_name)}\b[^"']*["'][^>]*>(?P<inner>.*?)</(?P=tag)>'''
    match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    return match.group("inner").strip() if match else ""


def _conteudo_html_sermao(sermao):
    html = _normalizar_mojibake(getattr(sermao, "conteudo_html", "") or "")
    if not html:
        return {"painel": "", "corpo": ""}

    painel = _extract_html_fragment(html, "key-panel")
    corpo = _extract_html_fragment(html, "reading-body")

    if corpo:
        return {"painel": painel, "corpo": corpo}

    article_match = re.search(
        r'''<article\b[^>]*class=["'][^"']*\breading-surface\b[^"']*["'][^>]*>(.*?)</article>''',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if article_match:
        return {"painel": painel, "corpo": article_match.group(1).strip()}

    body_match = re.search(r"<body\b[^>]*>(.*?)</body>", html, flags=re.IGNORECASE | re.DOTALL)
    if body_match:
        return {"painel": painel, "corpo": body_match.group(1).strip()}

    return {"painel": painel, "corpo": html.strip()}



def _serie_contexto(sermao):
    artigo_relacionado = getattr(sermao, "artigo_relacionado", None) or _buscar_artigo_relacionado(sermao)
    serie_canonica = _serie_canonica_sermao(sermao, artigo_relacionado)
    itens = []
    for item in Sermao.objects.filter(visivel=True).order_by("ordem", "titulo"):
        item_artigo = _buscar_artigo_relacionado(item)
        if _serie_canonica_sermao(item, item_artigo) != serie_canonica:
            continue
        _enriquecer_sermao(item, item_artigo)
        itens.append(item)

    anterior = None
    proximo = None
    for idx, item in enumerate(itens):
        if item.pk != sermao.pk:
            continue
        if idx > 0:
            anterior = itens[idx - 1]
        if idx + 1 < len(itens):
            proximo = itens[idx + 1]
        break
    return {
        "itens": itens,
        "total": len(itens),
        "anterior": anterior,
        "proximo": proximo,
        "anchor": _series_anchor(serie_canonica),
        "nome": serie_canonica,
    }


def _build_editorial_nav(*, tipo_atual: str, titulo: str, serie: str = "", artigo=None, sermao=None, serie_anchor: str = ""):
    breadcrumbs = [
        {"label": "Inicio", "url": "/"},
    ]
    if tipo_atual in {"sermao", "relatorio"}:
        breadcrumbs.append({"label": "Sermões", "url": "/sermoes/"})
        if serie:
            breadcrumbs.append({"label": serie, "url": f"/sermoes/#{serie_anchor}" if serie_anchor else "/sermoes/"})
    elif tipo_atual == "artigo":
        breadcrumbs.append({"label": "Artigos", "url": "/artigos/"})
        if artigo and getattr(artigo, "area", None):
            breadcrumbs.append({"label": artigo.area.nome, "url": "/artigos/"})
    breadcrumbs.append({"label": titulo, "url": ""})

    return {
        "breadcrumbs": breadcrumbs,
        "links": [],
        "titulo_atual": titulo,
        "serie": serie,
        "tipo_atual": tipo_atual,
    }


@usuario_habilitado_required
def lista_sermoes(request, origem="sermoes"):
    sermoes = list(Sermao.objects.filter(visivel=True).order_by("serie", "ordem", "titulo"))
    artigos_por_slug = {
        artigo.slug: artigo
        for artigo in Artigo.objects.filter(visivel=True, slug__in=[s.slug for s in sermoes if s.slug]).select_related("area", "autor")
    }
    for sermao in sermoes:
        artigo = artigos_por_slug.get((sermao.slug or "").strip()) or None
        _enriquecer_sermao(sermao, artigo)

    series = _series_index(sermoes)
    series_payload = []
    for serie, itens in series.items():
        qtd_com_relatorio = sum(1 for item in itens if getattr(item.relatorio_tecnico_pdf, "name", ""))
        series_payload.append(
            {
                "nome": serie,
                "anchor": _series_anchor(serie),
                "sermoes": itens,
                "total": len(itens),
                "com_relatorio": qtd_com_relatorio,
            }
        )

    selected_raw = (request.GET.get("serie") or "").strip()
    selected = None
    if series_payload:
        for bloco in series_payload:
            if selected_raw and selected_raw in {bloco["anchor"], bloco["nome"], slugify(bloco["nome"])}:
                selected = bloco
                break
        if selected is None:
            selected = series_payload[0]

    return render(
        request,
        "sermoes/lista.html",
        {
            "series": series_payload,
            "selected_serie": selected,
            "total_sermoes": len(sermoes),
            "total_series": len(series_payload),
            "origem_editorial": origem,
        },
    )


@usuario_habilitado_required
def detalhe_sermao(request, slug):
    sermao = get_object_or_404(Sermao, slug=slug, visivel=True)
    artigo_relacionado = _buscar_artigo_relacionado(sermao)
    _enriquecer_sermao(sermao, artigo_relacionado)
    serie_ctx = _serie_contexto(sermao)
    relacionados = list(
        Sermao.objects.filter(visivel=True, serie=sermao.serie).exclude(pk=sermao.pk).order_by("ordem", "titulo")[:6]
    )
    relacionados = [_enriquecer_sermao(item) for item in relacionados]
    arquivos = []
    for key, (field_name, label) in ARQUIVOS_SERMAO.items():
        field = getattr(sermao, field_name, None)
        if field:
            arquivos.append(
                {
                    "key": key,
                    "label": label,
                    "disponivel": bool(getattr(field, "name", "")),
                    "url": f"/sermoes/{sermao.slug}/arquivo/{key}/",
                }
            )

    return render(
        request,
        "sermoes/detalhe.html",
        {
            "sermao": sermao,
            "arquivos": arquivos,
            "artigo_relacionado": artigo_relacionado,
            "formatos": _formatos_disponiveis(sermao),
            "relacionados": relacionados,
            "serie_ctx": serie_ctx,
            "serie_exibicao": serie_ctx["nome"],
            "conteudo_sermao": _conteudo_html_sermao(sermao),
            "subtitulo_artefato": _resumo_editorial_valido(sermao.resumo, sermao.titulo_exibicao, getattr(artigo_relacionado, "titulo", "")),
            "imagem_editorial": _imagem_editorial(sermao, artigo_relacionado),
            "editorial_nav": _build_editorial_nav(
                tipo_atual="sermao",
                titulo=sermao.titulo_exibicao,
                serie=serie_ctx["nome"],
                artigo=artigo_relacionado,
                sermao=sermao,
                serie_anchor=serie_ctx["anchor"],
            ),
        },
    )


@usuario_habilitado_required
def detalhe_relatorio_tecnico(request, slug):
    sermao = get_object_or_404(Sermao, slug=slug, visivel=True)
    if not getattr(sermao.relatorio_tecnico_pdf, "name", ""):
        raise Http404("Estudo ainda nao associado a este sermão.")
    artigo_relacionado = _buscar_artigo_relacionado(sermao)
    _enriquecer_sermao(sermao, artigo_relacionado)
    serie_ctx = _serie_contexto(sermao)
    return render(
        request,
        "sermoes/relatorio.html",
        {
            "sermao": sermao,
            "artigo_relacionado": artigo_relacionado,
            "serie_ctx": serie_ctx,
            "serie_exibicao": serie_ctx["nome"],
            "conteudo_relatorio_html": _conteudo_html_dossie(sermao),
            "subtitulo_artefato": _resumo_editorial_valido(sermao.resumo, sermao.titulo_exibicao, getattr(artigo_relacionado, "titulo", "")),
            "imagem_editorial": _imagem_editorial(sermao, artigo_relacionado),
            "editorial_nav": _build_editorial_nav(
                tipo_atual="relatorio",
                titulo=f"Estudo - {sermao.titulo_exibicao}",
                serie=serie_ctx["nome"],
                artigo=artigo_relacionado,
                sermao=sermao,
                serie_anchor=serie_ctx["anchor"],
            ),
        },
    )


@usuario_habilitado_required
def baixar_arquivo_sermao(request, slug, kind):
    sermao = get_object_or_404(Sermao, slug=slug, visivel=True)
    meta = ARQUIVOS_SERMAO.get(kind)
    if not meta:
        raise Http404("Tipo de arquivo nao encontrado.")

    field_name, _label = meta
    field = getattr(sermao, field_name, None)
    if not field or not getattr(field, "name", ""):
        raise Http404("Arquivo ainda nao disponivel para este sermao.")

    arquivo = open_file(field, "rb")
    filename = Path(field.name).name
    return FileResponse(arquivo, as_attachment=True, filename=filename)
