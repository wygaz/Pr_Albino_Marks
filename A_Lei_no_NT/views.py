from django.shortcuts import render, get_object_or_404
from .models import Artigo

def lista_artigos(request):
    artigos = Artigo.objects.all().order_by('ordem')
    return render(request, 'A_Lei_no_NT/artigo_list.html', {'artigos': artigos})

def detalhe_artigo(request, slug):
    artigo = get_object_or_404(Artigo, slug=slug)
    return render(request, 'A_Lei_no_NT/artigo_detalhe.html', {'artigo': artigo})