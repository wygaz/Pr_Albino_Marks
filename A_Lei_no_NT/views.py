from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.urls import reverse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils import timezone
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from .models import Artigo
from .forms import ArtigoForm
from A_Lei_no_NT.utils_storage import open_file
from django.db import IntegrityError, transaction
from .utils import gerar_slug

def home(request):
    artigos = Artigo.objects.filter(visivel=True).order_by('-publicado_em')
    return render(request, 'A_Lei_no_NT/home.html')

def visualizar_artigo(request, slug):
    artigo = get_object_or_404(Artigo, slug=slug, visivel=True)
    return render(request, 'A_Lei_no_NT/visualizar_artigo.html', {'artigo': artigo})

def criar_artigo(request):
    if request.method == "POST":
        form = ArtigoForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if not obj.slug:
                obj.slug = gerar_slug(obj.titulo)
            try:
                with transaction.atomic():
                    obj.save()
            except IntegrityError:
                # colisão rara: gera outro e salva
                obj.slug = gerar_slug(obj.titulo)
                obj.save()
            form.save_m2m()
            messages.success(request, "Artigo criado com sucesso.")
            return redirect("listar_artigos")
    else:
        form = ArtigoForm()
    return render(request, "A_Lei_no_NT/criar_artigo.html", {"form": form})

def listar_artigos(request):
    artigos = Artigo.objects.filter(visivel=True).order_by('ordem', 'titulo')
    return render(request, 'A_Lei_no_NT/listar_artigos.html', {'artigos': artigos})

def biografia(request):
    return render(request, 'A_Lei_no_NT/biografia.html')

def motivacao_publicacao(request):
    return render(request, 'A_Lei_no_NT/motivacao_publicacao.html')

def artigos_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    y = h - 2*cm
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2*cm, y, "Lista de Artigos – Projeto Pr. Albino Marks")
    y -= 0.8*cm
    p.setFont("Helvetica", 9)
    p.drawString(2*cm, y, timezone.now().strftime("Gerado em %d/%m/%Y %H:%M"))
    y -= 1.0*cm

    p.setFont("Helvetica", 11)
    artigos = Artigo.objects.filter(visivel=True).order_by("-publicado_em")
    for art in artigos:
        linha = f"• {art.titulo}"
        if art.publicado_em:
            linha += f" — {art.publicado_em.strftime('%d/%m/%Y')}"
        for bloco in _wrap(linha, max_chars=100):
            if y < 2*cm:
                p.showPage()
                y = h - 2*cm
                p.setFont("Helvetica", 11)
            p.drawString(2*cm, y, bloco)
            y -= 0.55*cm
        y -= 0.25*cm

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
    f = open_file(art.arquivo_pdf, "rb")  # não use 'with' aqui
    return FileResponse(
        f,
        as_attachment=True,
        filename=f"{art.slug}.pdf",
        content_type="application/pdf",
    )

