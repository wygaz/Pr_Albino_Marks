from django.contrib import admin
from .models import Artigo, Area, Autor

@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = ('ordem','autor', 'visivel', 'publicado_em')  # Removido 'titulo'
    list_filter = ('autor', 'visivel')
    search_fields = ('autor__nome',)
    ordering = ('-publicado_em',)
    readonly_fields = ('slug', 'ordem', 'titulo')
    list_editable = ('visivel',)

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')  # Removido 'ordem', pois Area não possui esse campo
    search_fields = ('nome',)
    ordering = ('nome',)

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)
    ordering = ('nome',)
