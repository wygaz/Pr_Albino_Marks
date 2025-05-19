from django.urls import path
from . import views

app_name = 'A_Lei_no_NT'

urlpatterns = [
    path('artigos/', views.lista_artigos, name='lista_artigos'),
    path('artigos/<slug:slug>/', views.detalhe_artigo, name='detalhe_artigo'),
]
