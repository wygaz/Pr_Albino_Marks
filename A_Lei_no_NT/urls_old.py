from django.urls import path
from . import views

app_name = 'A_Lei_no_NT'

urlpatterns = [
    path('', views.lista_artigos, name='lista_artigos'),                      # Página principal de artigos
    path('novo/', views.criar_artigo, name='criar_artigo'),                   # Formulário de novo artigo (upload .docx)
    path('<slug:slug>/', views.visualizar_artigo, name='visualizar_artigo'), # Visualização do artigo pelo slug
]
