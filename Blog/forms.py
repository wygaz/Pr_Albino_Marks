# forms.py
from django import forms
from .models import Artigo, Autor, Area, Midia

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        fields = ['titulo', 'conteudo_html', 'autor', 'area', 'midia', 'data_publicacao', 'ordem']

class AutorForm(forms.ModelForm):
    class Meta:
        model = Autor
        fields = ['nome_autor', 'biografia', 'midia', 'foto']

class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['nome_area', 'descricao']

class MidiaForm(forms.ModelForm):
    class Meta:
        model = Midia
        fields = ['nome_midia', 'tipo', 'arquivo', 'descricao']