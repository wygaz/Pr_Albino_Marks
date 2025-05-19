from django.urls import path
from . import views

app_name = 'A_Lei_no_NT'

urlpatterns = [
    path('artigos/', views.artigo.list, name='artigo_lists'),
    path('artigos/<slug:slug>/', views.detalhe_artigo, name='detalhe_artigo'),
]
