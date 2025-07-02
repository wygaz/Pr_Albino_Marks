from django import forms
from .models import Artigo
from .utils import docx_para_html, gerar_slug, renomear_arquivo_word, renomear_imagem_capa

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        exclude = ('slug', 'conteudo_html')

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('arquivo_word'):
            docx_file = self.cleaned_data['arquivo_word']
            html, titulo_detectado = docx_para_html(docx_file)
            instance.conteudo_html = html
            titulo_final = titulo_detectado or instance.titulo or 'Título não definido'
            instance.titulo = titulo_final
            instance.slug = gerar_slug(titulo_final)
        if commit:
            instance.save()
        return instance
