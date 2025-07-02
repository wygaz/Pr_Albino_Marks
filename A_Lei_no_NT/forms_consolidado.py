
from django import forms
from .models import Artigo
from .utils import docx_para_html, gerar_slug

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        exclude = ('slug', 'conteudo_html')

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.cleaned_data.get('arquivo_word'):
            docx_file = self.cleaned_data['arquivo_word']
            html, titulo = docx_para_html(docx_file)

            instance.conteudo_html = html
            if not instance.titulo:
                instance.titulo = titulo or 'Título não definido'
            instance.slug = gerar_slug(instance.titulo)

        if commit:
            instance.save()
        return instance
