from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('artigos/', views.listar_artigos, name='listar_artigos'),
    path('criar/', views.criar_artigo, name='criar_artigo'),
    path('motivacao/', views.motivacao_publicacao, name='motivacao_publicacao'),
    path('biografia/', views.biografia, name='biografia'),
    path('<slug:slug>/', views.visualizar_artigo, name='visualizar_artigo'),
    
]

