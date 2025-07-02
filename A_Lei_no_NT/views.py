from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Artigo
from .forms import ArtigoForm
from django.core.paginator import Paginator

def home(request):
   return render(request, 'A_Lei_no_NT/home.html')

def listar_artigos(request):
    artigos = Artigo.objects.order_by('-publicado_em')
    paginator = Paginator(artigos, 10)
    pagina = request.GET.get('page')
    artigos_paginados = paginator.get_page(pagina)
    return render(request, 'A_Lei_no_NT/listar_artigos.html', {'artigos': artigos_paginados})

def visualizar_artigo(request, slug):
    artigo = get_object_or_404(Artigo, slug=slug)
    return render(request, 'A_Lei_no_NT/visualizar_artigo.html', {'artigo': artigo})

def biografia(request):
    artigos_sidebar = Artigo.objects.filter(visivel=True).order_by('-publicado_em')[:15]
    return render(request, 'A_Lei_no_NT/biografia.html', {
        'artigos_sidebar': artigos_sidebar
    })

def motivacao_publicacao(request):
    return render(request, 'A_Lei_no_NT/motivacao_publicacao.html')


def criar_artigo(request):
    if request.method == 'POST':
        form = ArtigoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                artigo = form.save()
                print(f"✅ Artigo salvo: {artigo.titulo} | slug: {artigo.slug}")
                messages.success(request, 'Artigo criado com sucesso.')
                return redirect('A_Lei_no_NT:visualizar_artigo', slug=artigo.slug)
            except Exception as e:
                print("🚨 Erro ao salvar o artigo:")
                print(e)
                messages.warning(request, f"Erro ao salvar o artigo: {e}")
        else:
            print("⚠️ Erros no formulário:")
            print(form.errors)
    else:
        form = ArtigoForm()
    
    return render(request, 'A_Lei_no_NT/criar_artigo.html', {'form': form})
