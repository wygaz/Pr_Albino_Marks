from io import BytesIO

from django.contrib.auth import login
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import strip_tags
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from .access import get_or_create_acesso_usuario, sincronizar_grupo_habilitado
from .forms import AceiteAcessoForm, ArtigoForm, CadastroVisitanteForm
from .models import Area, Artigo
from .utils import gerar_slug
from A_Lei_no_NT.utils_storage import open_file
from django.db.models import Count, Q, F


def _build_editorial_nav_artigo(artigo, sermoes_relacionados):
    links = [
        {"label": "Voltar para o acervo", "url": "/sermoes/"},
    ]
    if artigo.area:
        links.append({"label": f"Serie: {artigo.area.nome}", "url": f"/sermoes/?serie={artigo.area.nome}"})
    if sermoes_relacionados:
        links.append({"label": "Ver sermões relacionados", "url": f"/sermoes/{sermoes_relacionados[0].slug}/"})
    return {
        "breadcrumbs": [
            {"label": "Inicio", "url": "/"},
            {"label": "Acervo Editorial", "url": "/sermoes/"},
            {"label": _titulo_exibicao_artigo(artigo), "url": ""},
        ],
        "links": [],
        "titulo_atual": _titulo_exibicao_artigo(artigo),
        "serie": artigo.area.nome if artigo.area else "",
        "tipo_atual": "artigo",
    }


def _dossies_relacionados(sermoes_relacionados):
    return [sermao for sermao in sermoes_relacionados if getattr(sermao.relatorio_tecnico_pdf, "name", "")]


def _titulo_exibicao_artigo(artigo):
    conteudo = artigo.conteudo_html or ""
    for tag in ("h1", "h2"):
        m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", conteudo, flags=re.IGNORECASE | re.DOTALL)
        if m:
            titulo = strip_tags(m.group(1)).strip()
            if titulo:
                return titulo
    return artigo.titulo



def _resumo_artigo_editorial(artigo):
    titulo = (_titulo_exibicao_artigo(artigo) or "").strip().lower()
    for item in (getattr(artigo, "conteudo_html", "") or "",):
        pass
    return "Leitura integral do artigo com acesso aos desdobramentos editoriais relacionados."

def listar_areas(request):
    """
    Página principal: lista apenas as áreas (temas) disponíveis.
    """
    areas = Area.objects.all().order_by("nome")
    return render(request, "A_Lei_no_NT/listar_areas.html", {"areas": areas})


def listar_artigos_por_area(request, area_slug):
    """
    Lista os artigos de uma área específica.
    """
    area = get_object_or_404(Area, slug=area_slug)  # se o campo não for 'slug', ajuste aqui
    artigos = Artigo.objects.filter(area=area, visivel=True).order_by("ordem", "titulo")


    context = {
        "area": area,
        "artigos": artigos,
        "page_obj": None,  # se você usar paginação depois, dá pra trocar
    }
    return render(request, "A_Lei_no_NT/listar_arquivos.html", context)




def home(request):
    artigos = Artigo.objects.filter(visivel=True).order_by("-publicado_em")
    return render(request, "A_Lei_no_NT/home.html", {"artigos": artigos})


def visualizar_artigo(request, slug):
    from sermoes.models import Sermao
    from sermoes.views import _enriquecer_sermao

    artigo = get_object_or_404(Artigo, slug=slug, visivel=True)

    # opcional: não contar staff/admin
    if not (request.user.is_authenticated and request.user.is_staff):
        session_key = f"viewed_artigo_{artigo.pk}"
        if not request.session.get(session_key):
            Artigo.objects.filter(pk=artigo.pk).update(views=F("views") + 1)
            request.session[session_key] = True

    # opcional: trazer o valor atualizado pra exibir na página
    artigo.refresh_from_db(fields=["views"])

    sermoes_relacionados = list(
        Sermao.objects.filter(visivel=True, slug=artigo.slug).order_by("ordem", "titulo")[:4]
    )
    if not sermoes_relacionados:
        sermoes_relacionados = list(
            Sermao.objects.filter(visivel=True, titulo__iexact=artigo.titulo).order_by("ordem", "titulo")[:4]
        )
    sermoes_relacionados = [_enriquecer_sermao(sermao, artigo) for sermao in sermoes_relacionados]
    dossies_relacionados = _dossies_relacionados(sermoes_relacionados)
    artigo.titulo_exibicao = _titulo_exibicao_artigo(artigo)

    return render(
        request,
        "A_Lei_no_NT/visualizar_artigo.html",
        {
            "artigo": artigo,
            "sermoes_relacionados": sermoes_relacionados,
            "dossies_relacionados": dossies_relacionados,
            "subtitulo_artefato": _resumo_artigo_editorial(artigo),
            "imagem_editorial": artigo.imagem_capa,
            "editorial_nav": _build_editorial_nav_artigo(artigo, sermoes_relacionados),
        },
    )


# View unificada: cria e edita
def artigo_form(request, slug=None):
    obj = get_object_or_404(Artigo, slug=slug) if slug else None
    titulo_pagina = "Editar artigo" if obj else "Novo artigo"

    if request.method == "POST":
        form = ArtigoForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            artigo = form.save(commit=False)
            if not artigo.slug:
                artigo.slug = gerar_slug(artigo.titulo)
            try:
                with transaction.atomic():
                    artigo.save()
                    form.save_m2m()
            except IntegrityError:
                # colisão raríssima — gera outro slug e salva
                artigo.slug = gerar_slug(artigo.titulo)
                artigo.save()
                form.save_m2m()

            messages.success(request, "Artigo salvo com sucesso.")
            return redirect("A_Lei_no_NT:visualizar_artigo", slug=artigo.slug)
    else:
        form = ArtigoForm(instance=obj)

    return render(
        request,
        "A_Lei_no_NT/artigo_form.html",
        {"form": form, "obj": obj, "titulo_pagina": titulo_pagina},
    )


def listar_artigos(request):
    areas = Area.objects.filter(visivel=True).order_by("nome")
    artigos = (
        Artigo.objects.filter(visivel=True)
        .select_related("area", "autor")
        .order_by("area__nome", "ordem", "titulo")
    )
    return render(
        request,
        "A_Lei_no_NT/listar_artigos.html",
        {
            "areas": areas,
            "artigos": artigos,
            "page_obj": None,
        },
    )



def biografia(request):
    return render(request, "A_Lei_no_NT/biografia.html")


def motivacao_publicacao(request):
    return render(request, "A_Lei_no_NT/motivacao_publicacao.html")


def cadastro_visitante(request):
    if request.user.is_authenticated:
        acesso = get_or_create_acesso_usuario(request.user)
        if acesso.acesso_liberado:
            return redirect("sermoes:lista")
        return redirect("A_Lei_no_NT:aceite_acesso")

    if request.method == "POST":
        form = CadastroVisitanteForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            get_or_create_acesso_usuario(user)
            messages.success(request, "Cadastro criado. Falta apenas concluir os aceites para liberar o acesso.")
            return redirect("A_Lei_no_NT:aceite_acesso")
    else:
        form = CadastroVisitanteForm()

    return render(request, "A_Lei_no_NT/cadastro.html", {"form": form})


def aceite_acesso(request):
    if not request.user.is_authenticated:
        return redirect(f"/conta/entrar/?next=/conta/aceite/")

    acesso = get_or_create_acesso_usuario(request.user)
    if acesso.acesso_liberado:
        destino = request.GET.get("next") or "/sermoes/"
        return redirect(destino)

    if request.method == "POST":
        form = AceiteAcessoForm(request.POST)
        if form.is_valid():
            acesso.registrar_aceite()
            sincronizar_grupo_habilitado(request.user)
            messages.success(request, "Aceite registrado. O acesso aos sermoes e relatorios foi liberado.")
            destino = request.POST.get("next") or request.GET.get("next") or "/sermoes/"
            return redirect(destino)
    else:
        form = AceiteAcessoForm()

    return render(
        request,
        "A_Lei_no_NT/aceite_acesso.html",
        {
            "form": form,
            "acesso": acesso,
            "next_url": request.GET.get("next", "/sermoes/"),
            "termos_versao": acesso.termos_versao,
            "lgpd_versao": acesso.lgpd_versao,
        },
    )


def artigos_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    y = h - 2 * cm
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2 * cm, y, "Lista de Artigos – Projeto Pr. Albino Marks")
    y -= 0.8 * cm
    p.setFont("Helvetica", 9)
    p.drawString(2 * cm, y, timezone.now().strftime("Gerado em %d/%m/%Y %H:%M"))
    y -= 1.0 * cm

    p.setFont("Helvetica", 11)
    artigos = Artigo.objects.filter(visivel=True).order_by("-publicado_em")
    for art in artigos:
        linha = f"• {art.titulo}"
        if art.publicado_em:
            linha += f" — {art.publicado_em.strftime('%d/%m/%Y')}"
        for bloco in _wrap(linha, max_chars=100):
            if y < 2 * cm:
                p.showPage()
                y = h - 2 * cm
                p.setFont("Helvetica", 11)
            p.drawString(2 * cm, y, bloco)
            y -= 0.55 * cm
        y -= 0.25 * cm

    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="lista_de_artigos.pdf")


def _wrap(texto, max_chars=100):
    out, linha, cont = [], [], 0
    for w in texto.split():
        add = len(w) + (1 if cont else 0)
        if cont + add > max_chars:
            out.append(" ".join(linha))
            linha, cont = [w], len(w)
        else:
            linha.append(w)
            cont += add
    if linha:
        out.append(" ".join(linha))
    return out


def artigo_pdf_download(request, slug):
    art = get_object_or_404(Artigo, slug=slug, visivel=True)
    if not art.arquivo_pdf:
        raise Http404("PDF ainda não foi gerado para este artigo.")
    f = open_file(art.arquivo_pdf, "rb")  # não use 'with' aqui (o FileResponse fecha)
    return FileResponse(
        f,
        as_attachment=True,
        filename=f"{art.slug}.pdf",
        content_type="application/pdf",
    )
