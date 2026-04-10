# sermoes\admin.py
from django.contrib import admin
from .models import Sermao


@admin.register(Sermao)
class SermaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'serie', 'visivel', 'ordem', 'data_publicacao')
    list_filter = ('visivel', 'serie', 'data_publicacao')
    search_fields = ('titulo', 'serie', 'resumo')
    ordering = ('ordem', 'titulo')
    fields = (
        'titulo', 'slug', 'serie', 'resumo', 'conteudo_html',
        'pdf_tablet', 'pdf_a4', 'pdf_a5', 'relatorio_tecnico_pdf', 'docx_a4', 'imagem_capa',
        'visivel', 'ordem', 'data_publicacao',
    )
