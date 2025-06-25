from django import forms
from django.forms import DateTimeInput
from .models import Artigo
from .utils import gerar_titulo_numerado, gerar_slug, docx_para_html

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        exclude = ('slug', 'conteudo_html', 'ordem', 'publicado_em')

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Se veio um arquivo .docx, processar para HTML e título
        if self.cleaned_data.get('arquivo_word'):
            docx_file = self.cleaned_data['arquivo_word']
            html, titulo_extraido = docx_para_html(docx_file)
            instance.conteudo_html = html

            if not instance.titulo:
                instance.titulo = titulo_extraido

        # Se houver título, gerar numeração
        if instance.titulo:
            instance.titulo = gerar_titulo_numerado(instance.titulo)

        # Gerar slug único com base no título numerado
        if not instance.slug:
            instance.slug = gerar_slug(instance.titulo)

        if commit:
            instance.save()

        return instance
    
    def save(self, commit=True):
        instance = super().save(commit=False)

        # Processar conteúdo Word, se houver
        if self.cleaned_data.get('arquivo_word'):
            docx_file = self.cleaned_data['arquivo_word']
            html, titulo_extraido = docx_para_html(docx_file)
            instance.conteudo_html = html
            if not instance.titulo:
                instance.titulo = titulo_extraido

        # Aplica a lógica de título numerado
        if instance.titulo:
            instance.titulo = gerar_titulo_numerado(instance.titulo)

        # Gera slug único com base no novo título
        if not instance.slug:
            instance.slug = gerar_slug(instance.titulo)

        if commit:
            instance.save()
        return instance
