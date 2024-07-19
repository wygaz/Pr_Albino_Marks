# A_Lei_no_NT/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('artigos/', views.artigo_list, name='artigo_list'),
    path('artigos/<str:titulo>/', views.artigo_detalhe, name='artigo_detalhe'),
#    path('', index, name='index'),
#    path('artigos/', artigo_list, name='artigo_list'),
    path('artigos/create/', views.artigo_create, name='artigo_create'),
    path('artigos/update/<int:id>/', views.artigo_update, name='artigo_update'),
    path('artigos/delete/<int:id>/', views.artigo_delete, name='artigo_delete'),
#    path('artigos/<str:nome_arquivo>/', artigo_detalhe, name='artigo_detalhe'),
    
    path('autores/', views.autor_list, name='autor_list'),
    path('autores/<int:id>/', views.autor_detalhe, name='autor_detalhe'),
    path('autores/create/', views.autor_create, name='autor_create'),
    path('autores/update/<int:id>/', views.autor_update, name='autor_update'),
    path('autores/delete/<int:id>/',views. autor_delete, name='autor_delete'),

    path('areas/', views.area_list, name='area_list'),
    path('areas/<int:id>/', views.area_detalhe, name='area_detalhe'),
    path('areas/create/', views.area_create, name='area_create'),
    path('areas/update/<int:id>/', views.area_update, name='area_update'),
    path('areas/delete/<int:id>/', views.area_delete, name='area_delete'),

    path('midias/', views.midia_list, name='midia_list'),
    path('midias/<int:id>/', views.midia_detalhe, name='midia_detalhe'),
    path('midias/create/', views.midia_create, name='midia_create'),
    path('midias/update/<int:id>/', views.midia_update, name='midia_update'),
    path('midias/delete/<int:id>/', views.midia_delete, name='midia_delete'),
]
