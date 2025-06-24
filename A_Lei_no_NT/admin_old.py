from django.contrib import admin
from A_Lei_no_NT.models import Artigo, Autor, Area
from A_Lei_no_NT.utils import gerar_slug

@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = ('autor', 'publicado_em', 'visivel')
    search_fields = ('titulo', 'autor__nome')
    list_filter = ('visivel', 'publicado_em')
    readonly_fields = ('titulo','visualizar_conteudo_html', 'slug')  # slug

    def save_model(self, request, obj, form, change):
        if not obj.slug and obj.titulo:
            obj.slug = gerar_slug(obj.titulo)
        super().save_model(request, obj, form, change)

    fieldsets = (
        (None, {
            'fields': ('titulo', 'slug', 'autor', 'area', 'visivel', 'ordem', 'data_publicacao')
        }),
        ('Conteúdo', {
            'fields': ('visualizar_conteudo_html', 'arquivo_word', 'imagem_capa', 'midia')
        }),
    )

    def visualizar_conteudo_html(self, obj):
        return obj.conteudo_html if obj.conteudo_html else "(sem conteúdo)"

    visualizar_conteudo_html.allow_tags = True
    visualizar_conteudo_html.short_description = "Conteúdo HTML Renderizado"

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
