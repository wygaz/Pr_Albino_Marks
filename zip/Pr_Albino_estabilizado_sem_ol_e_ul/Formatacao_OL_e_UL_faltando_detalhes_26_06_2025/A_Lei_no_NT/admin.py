from django.contrib import admin
from .models import Artigo, Area, Autor
from . import mensagens

@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = ('ordem', 'titulo', 'autor', 'visivel', 'publicado_em')
    list_filter = ('autor', 'visivel')
    search_fields = ('autor__nome',)
    ordering = ('-publicado_em',)
    readonly_fields = ('slug', 'ordem', 'titulo')
    list_editable = ('visivel',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        mensagens.informar_titulo_ajustado(request, obj.titulo)
        mensagens.sucesso_artigo_salvo(request)

        if not obj.visivel:
            mensagens.aviso_artigo_oculto(request)

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
