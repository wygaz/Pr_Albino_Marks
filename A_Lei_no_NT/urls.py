from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_artigos, name='lista_artigos'),  # https://localhost:8000/artigos/
    path('criar/', views.criar_artigo, name='criar_artigo'),  # https://localhost:8000/artigos/criar/
    path('<slug:slug>/', views.visualizar_artigo, name='visualizar_artigo'),  # https://localhost:8000/artigos/<slug>/
]
