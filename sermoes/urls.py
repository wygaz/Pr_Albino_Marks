from django.urls import path
from .views import baixar_arquivo_sermao, detalhe_relatorio_tecnico, detalhe_sermao, lista_sermoes

app_name = 'sermoes'

urlpatterns = [
    path('', lista_sermoes, name='lista'),
    path('<slug:slug>/arquivo/<str:kind>/', baixar_arquivo_sermao, name='arquivo'),
    path('<slug:slug>/relatorio/', detalhe_relatorio_tecnico, name='relatorio'),
    path('<slug:slug>/', detalhe_sermao, name='detalhe'),
]
