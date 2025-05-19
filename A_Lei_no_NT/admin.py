from django.contrib import admin
from .models import Artigo, Autor, Area, Midia

@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'area', 'midia')
    search_fields = ('titulo', 'autor__nome', 'area__nome')
    list_filter = ('autor', 'area')

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    list_filter = ('nome',)

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    list_filter = ('nome',)

@admin.register(Midia)
class MidiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'arquivo')  # tipo/descricao removidos pois não existem no model
    search_fields = ('titulo',)
    list_filter = ()
