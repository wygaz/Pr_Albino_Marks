import tempfile
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils import timezone
from io import BytesIO
from .models import Artigo
from .forms import ArtigoForm
from django.shortcuts import redirect

def home(request):
    artigos = Artigo.objects.filter(visivel=True).order_by('-publicado_em')
    return render(request, 'A_Lei_no_NT/home.html')

def visualizar_artigo(request, slug):
    artigo = get_object_or_404(Artigo, slug=slug, visivel=True)
    return render(request, 'A_Lei_no_NT/visualizar_artigo.html', {'artigo': artigo})

def criar_artigo(request):
    if request.method == 'POST':
        form = ArtigoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Artigo salvo com sucesso!')
                return redirect('A_Lei_no_NT:home')
            except Exception as e:
                erro_msg = f"Erro ao salvar o artigo: {str(e)}"
                print(f"\n🚨 {erro_msg}")
                messages.error(request, erro_msg)
    else:
        form = ArtigoForm()
    return render(request, 'A_Lei_no_NT/artigo_form.html', {'form': form})


def artigo_pdf(request, slug):
    artigo = get_object_or_404(Artigo, slug=slug)
    html_string = render_to_string("A_Lei_no_NT/artigo_pdf.html", {"artigo": artigo})

    pdf_file = BytesIO()
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(pdf_file)
    pdf_file.seek(0)

    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{artigo.slug}.pdf"'
    return response

def listar_artigos(request):
    artigos = Artigo.objects.filter(visivel=True).order_by('ordem', 'titulo')
    return render(request, 'A_Lei_no_NT/listar_artigos.html', {'artigos': artigos})

def biografia(request):
    return redirect('A_Lei_no_NT:visualizar_artigo', slug='apresentacao-do-pastor-albino-marks')

def motivacao_publicacao(request):
    return render(request, 'A_Lei_no_NT/motivacao_publicacao.html')
