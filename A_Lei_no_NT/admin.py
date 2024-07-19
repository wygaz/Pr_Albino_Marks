# A_Lei_no_NT/admin.py
from django.contrib import admin
from .models import Artigo, Autor, Area, Midia

@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'area', 'midia')
    search_fields = ('titulo', 'autor__nome_autor', 'area__nome_area')
    list_filter = ('autor', 'area')

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nome_autor', 'biografia')
    search_fields = ('nome_autor',)
    list_filter = ('nome_autor',)

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nome_area',)
    search_fields = ('nome_area',)

@admin.register(Midia)
class MidiaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'descricao', 'arquivo')
    search_fields = ('tipo', 'descricao')
    list_filter = ('tipo',)
