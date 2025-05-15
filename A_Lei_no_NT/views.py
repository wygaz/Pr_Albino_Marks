# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.safestring import mark_safe
from .models import Artigo, Autor, Area, Midia
from .forms import ArtigoForm, AutorForm, AreaForm, MidiaForm
import logging
from django.conf import settings
import os
import re
from unidecode import unidecode
from django.http import JsonResponse

logger = logging.getLogger(__name__)

from django.shortcuts import render

# View para a página inicial
def index(request):
    order = request.GET.get('order', 'ordem')
    artigos = Artigo.objects.all().order_by(order)
    return render(request, 'A_Lei_no_NT/index.html', {'artigos': artigos})

# Views para Artigo
def artigo_detalhe(request, titulo):
    artigo = get_object_or_404(Artigo, titulo=titulo)
    order = request.GET.get('order', 'ordem')
    artigos = Artigo.objects.all().order_by(order)
    return render(request, 'A_Lei_no_NT/artigo_detalhe.html', {'artigo': artigo, 'artigos': artigos})


def artigo_list(request):
    order = request.GET.get('order', 'ordem')
    artigos = Artigo.objects.all().order_by(order)
    print("Ordenando por:", order)
    for artigo in artigos:
        print(artigo.titulo, artigo.autor.nome_autor, artigo.ordem)
    return render(request, 'A_Lei_no_NT/artigo_list.html', {'artigos': artigos})

def artigo_create(request):
    logger.info("Entrou na função artigo_create")
    if request.method == 'POST':
        form = ArtigoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('artigo_list')
    else:
        form = ArtigoForm()
    return render(request, 'A_Lei_no_NT/artigo_form.html', {'form': form})

def artigo_update(request, id):
    logger.info(f"Entrou na função artigo_update com id={id}")
    artigo = get_object_or_404(Artigo, id=id)
    if request.method == 'POST':
        form = ArtigoForm(request.POST, request.FILES, instance=artigo)
        if form.is_valid():
            form.save()
            return redirect('artigo_list')
    else:
        form = ArtigoForm(instance=artigo)
    return render(request, 'A_Lei_no_NT/artigo_form.html', {'form': form})

def artigo_delete(request, id):
    logger.info(f"Entrou na função artigo_delete com id={id}")
    artigo = get_object_or_404(Artigo, id=id)
    if request.method == 'POST':
        artigo.delete()
        return redirect('artigo_list')
    return render(request, 'A_Lei_no_NT/artigo_confirm_delete.html', {'artigo': artigo})

# Views para Autor
def autor_list(request):
    autores = Autor.objects.all()
    return render(request, 'A_Lei_no_NT/autor_list.html', {'autores': autores})

def autor_detalhe(request, id):
    autor = get_object_or_404(Autor, pk=id)
    return render(request, 'A_Lei_no_NT/autor_detalhe.html', {'autor': autor})

def autor_create(request):
    if request.method == 'POST':
        form = AutorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('autor_list')
    else:
        form = AutorForm()
    return render(request, 'A_Lei_no_NT/autor_form.html', {'form': form})

def autor_update(request, id):
    autor = get_object_or_404(Autor, id=id)
    if request.method == 'POST':
        form = AutorForm(request.POST, request.FILES, instance=autor)
        if form.is_valid():
            form.save()
            return redirect('autor_list')
    else:
        form = AutorForm(instance=autor)
    return render(request, 'A_Lei_no_NT/autor_form.html', {'form': form})

def autor_delete(request, id):
    autor = get_object_or_404(Autor, id=id)
    if request.method == 'POST':
        autor.delete()
        return redirect('autor_list')
    return render(request, 'A_Lei_no_NT/autor_confirm_delete.html', {'autor': autor})

# Views para Area
def area_list(request):
    areas = Area.objects.all()
    return render(request, 'A_Lei_no_NT/area_list.html', {'areas': areas})

def area_detalhe(request, id):
    area = get_object_or_404(Area, id=id)
    return render(request, 'A_Lei_no_NT/area_detalhe.html', {'area': area})

def area_create(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('area_list')
    else:
        form = AreaForm()
    return render(request, 'A_Lei_no_NT/area_form.html', {'form': form})

def area_update(request, id):
    area = get_object_or_404(Area, id=id)
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            return redirect('area_list')
    else:
        form = AreaForm(instance=area)
    return render(request, 'A_Lei_no_NT/area_form.html', {'form': form})

def area_delete(request, id):
    area = get_object_or_404(Area, id=id)
    if request.method == 'POST':
        area.delete()
        return redirect('area_list')
    return render(request, 'A_Lei_no_NT/area_confirm_delete.html', {'area': area})

# Views para Midia
def midia_list(request):
    midias = Midia.objects.all()
    return render(request, 'A_Lei_no_NT/midia_list.html', {'midias': midias})

def midia_detalhe(request, id):
    midia = get_object_or_404(Midia, id=id)
    return render(request, 'A_Lei_no_NT/midia_detalhe.html', {'midia': midia})

def midia_create(request):
    if request.method == 'POST':
        form = MidiaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('midia_list')
    else:
        form = MidiaForm()
    return render(request, 'A_Lei_no_NT/midia_form.html', {'form': form})

def midia_update(request, id):
    midia = get_object_or_404(Midia, id=id)
    if request.method == 'POST':
        form = MidiaForm(request.POST, request.FILES, instance=midia)
        if form.is_valid():
            form.save()
            return redirect('midia_list')
    else:
        form = MidiaForm(instance=midia)
    return render(request, 'A_Lei_no_NT/midia_form.html', {'form': form})

def midia_delete(request, id):
    midia = get_object_or_404(Midia, id=id)
    if request.method == 'POST':
        midia.delete()
        return redirect('midia_list')
    return render(request, 'A_Lei_no_NT/midia_confirm_delete.html', {'midia': midia})