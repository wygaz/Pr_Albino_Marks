from io import BytesIO

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from .forms import ArtigoForm
from .models import Area, Artigo
from .utils import gerar_slug
from A_Lei_no_NT.utils_storage import open_file
from django.db.models import Count, Q, F


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
    artigos = (
        Artigo.objects
        .filter(area=area)
        .order_by("-publicado_em", "-id")
    )

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
    artigo = get_object_or_404(Artigo, slug=slug, visivel=True)

    # opcional: não contar staff/admin
    if not (request.user.is_authenticated and request.user.is_staff):
        session_key = f"viewed_artigo_{artigo.pk}"
        if not request.session.get(session_key):
            Artigo.objects.filter(pk=artigo.pk).update(views=F("views") + 1)
            request.session[session_key] = True

    # opcional: trazer o valor atualizado pra exibir na página
    artigo.refresh_from_db(fields=["views"])

    return render(request, "A_Lei_no_NT/visualizar_artigo.html", {"artigo": artigo})


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
    """Página única: filtros de área no topo e lista de artigos abaixo."""
    areas = Area.objects.filter(visivel=True).order_by("nome")
    artigos = (
        Artigo.objects
        .filter(visivel=True)
        .select_related("area")
        .order_by("ordem", "titulo")
    )
    context = {
        "areas": areas,
        "artigos": artigos,
        "page_obj": None,  # reservado para futura paginação, se você quiser depois
    }
    return render(request, "A_Lei_no_NT/listar_artigos.html", context)



def biografia(request):
    return render(request, "A_Lei_no_NT/biografia.html")


def motivacao_publicacao(request):
    return render(request, "A_Lei_no_NT/motivacao_publicacao.html")


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
