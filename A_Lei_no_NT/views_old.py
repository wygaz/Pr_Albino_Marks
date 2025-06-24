from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Artigo
from .forms import ArtigoForm
from A_Lei_no_NT.utils import docx_para_html, gerar_slug

def home(request):
    return render(request, 'home.html')

def lista_artigos(request):
    lista = Artigo.objects.all().order_by('-publicado_em')
    paginator = Paginator(lista, 10)
    pagina = request.GET.get('page')
    artigos = paginator.get_page(pagina)
    return render(request, 'A_Lei_no_NT/artigo_lista.html', {'artigos': artigos})

def visualizar_artigo(request, slug):
    artigo = get_object_or_404(Artigo, slug=slug)
    return render(request, 'A_Lei_no_NT/artigo_visualizar.html', {'artigo': artigo})

def criar_artigo(request):
    if request.method == 'POST':
        form = ArtigoForm(request.POST, request.FILES)
        if form.is_valid():
            artigo = form.save(commit=False)

            arquivo = form.cleaned_data.get('arquivo_word')
            if arquivo:
                html, titulo = docx_para_html(arquivo)
                artigo.conteudo_html = html
                if not artigo.titulo or artigo.titulo.strip() == "-":
                    artigo.titulo = titulo
                if not artigo.slug or artigo.slug.strip() == "":
                    artigo.slug = gerar_slug(titulo)

            artigo.save()
            messages.success(request, 'Artigo salvo com sucesso!')
            return redirect('lista_artigos')
    else:
        form = ArtigoForm()

    return render(request, 'A_Lei_no_NT/artigo_form.html', {'form': form})
