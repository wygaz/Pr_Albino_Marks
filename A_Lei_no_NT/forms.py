from django import forms
from django.forms import DateTimeInput
from .models import Artigo
from .utils import docx_para_html, gerar_slug

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        exclude = ('slug', 'conteudo_html', 'titulo')  # gerados automaticamente

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Permitir campo opcional para data/hora de publicação
        self.fields['publicado_em'].required = False
        self.fields['publicado_em'].widget = DateTimeInput(attrs={'type': 'datetime-local'})
        self.fields['visivel'].initial = True  # torna visível por padrão

        # Deixar o campo 'visivel' opcional com valor default False
        self.fields['visivel'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Processar documento Word
        if self.cleaned_data.get('arquivo_word'):
            docx_file = self.cleaned_data['arquivo_word']
            html, titulo = docx_para_html(docx_file)
            instance.conteudo_html = html
            if not instance.titulo:
                instance.titulo = titulo

        # Gerar slug com base no título, se ainda não tiver
        if not instance.slug and instance.titulo:
            instance.slug = gerar_slug(instance.titulo)

        # Garantir valor padrão para 'visivel'
        if instance.visivel is None:
            instance.visivel = False

        # Salvar instância
        if commit:
            instance.save()
        return instance
