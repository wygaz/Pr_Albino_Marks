from django import forms
from .models import Artigo
from .utils import docx_para_html, gerar_slug
from django.db.models import Max

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        exclude = ('titulo', 'slug', 'conteudo_html', 'ordem')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limita visualmente a seleção no navegador para arquivos .docx
        self.fields['arquivo_word'].widget.attrs.update({'accept': '.docx'})

    def clean_arquivo_word(self):
        arquivo = self.cleaned_data.get('arquivo_word')
        if arquivo and not arquivo.name.lower().endswith('.docx'):
            raise forms.ValidationError("Somente arquivos .docx são permitidos.")
        return arquivo

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Extrai conteúdo HTML e título do arquivo Word
        arquivo = self.cleaned_data.get('arquivo_word')
        if arquivo:
            html, titulo_extraido = docx_para_html(arquivo)
            instance.conteudo_html = html
            if not instance.titulo or instance.titulo.strip() == '':
                instance.titulo = titulo_extraido.strip()
            if not instance.slug or instance.slug.strip() == '':
                instance.slug = gerar_slug(instance.titulo)

        # Define ordem automática apenas se for novo (sem PK)
        if not instance.pk and instance.ordem is None:
            maior_ordem = Artigo.objects.aggregate(Max('ordem'))['ordem__max'] or 0
            instance.ordem = maior_ordem + 1

        if commit:
            instance.save()
        return instance
