from django.urls import path
from . import views

app_name = 'A_Lei_no_NT'

urlpatterns = [
    path('', views.home, name='home'),
    path('artigos/', views.listar_artigos, name='listar_artigos'),
    path('criar/', views.criar_artigo, name='criar_artigo'),
    path('motivacao/', views.motivacao_publicacao, name='motivacao_publicacao'),
    path('biografia/', views.biografia, name='biografia'),
    path('<slug:slug>/', views.visualizar_artigo, name='visualizar_artigo'),
    path("artigos/pdf/", views.artigos_pdf, name="artigos_pdf"),
    path("artigo/<slug:slug>/pdf/", views.artigo_pdf_download, name="artigo_pdf_download"),
 #   path('artigo/<slug:slug>/pdf/', views.artigo_pdf, name='artigo_pdf'),
]

