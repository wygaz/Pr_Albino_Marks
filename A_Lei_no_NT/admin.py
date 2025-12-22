# A_Lei_no_NT/admin.py
from django.contrib import admin
from .models import Artigo, Area, Autor
from . import mensagens
from .forms import ArtigoForm

@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    form = ArtigoForm

    # título como link, ordem logo ao lado + contador
    list_display = ("titulo", "ordem", "autor", "area", "visivel", "publicado_em", "views")
    list_display_links = ("titulo",)  # só o título é clicável

    list_filter = ("area", "autor", "visivel")
    search_fields = ("titulo", "slug", "autor__nome", "area__nome")
    ordering = ("ordem", "-publicado_em")

    # slug e views não devem ser editados manualmente
    readonly_fields = ("slug", "views")

    # editar ordem e visível direto na lista
    list_editable = ("ordem", "visivel")

    def save_model(self, request, obj, form, change):
        """
        Mantém a mesma lógica de mensagens que você já tinha.
        O slug agora é recalculado no models.py quando o título muda.
        """
        super().save_model(request, obj, form, change)

        mensagens.informar_titulo_ajustado(request, obj.titulo)
        mensagens.sucesso_artigo_salvo(request)

        if not obj.visivel:
            mensagens.aviso_artigo_oculto(request)


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("id", "nome")
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ("id", "nome")
    search_fields = ("nome",)
    ordering = ("nome",)
