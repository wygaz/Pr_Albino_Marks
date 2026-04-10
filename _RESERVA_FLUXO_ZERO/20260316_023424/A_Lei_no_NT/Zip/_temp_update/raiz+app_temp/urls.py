from django.urls import path
from . import views

app_name = "A_Lei_no_NT"

urlpatterns = [
    path("", views.home, name="home"),

    # Artigos
    path("artigos/", views.listar_artigos, name="listar_artigos"),
    path("artigos/novo/", views.artigo_form, name="criar_artigo"),
    path("artigos/<slug:slug>/editar/", views.artigo_form, name="editar_artigo"),
    path("artigos/<slug:slug>/pdf/", views.artigo_pdf_download, name="artigo_pdf_download"),
    path("artigos/pdf/", views.artigos_pdf, name="artigos_pdf"),

    # Páginas
    path("motivacao/", views.motivacao_publicacao, name="motivacao_publicacao"),
    path("biografia/", views.biografia, name="biografia"),

    # Visualização do artigo por slug (por último para não “capturar” rotas acima)
    path("<slug:slug>/", views.visualizar_artigo, name="visualizar_artigo"),
]
