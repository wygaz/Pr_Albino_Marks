from django import forms
from .models import Artigo
from .utils import docx_para_html, gerar_slug
from django.db.models import Count

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        exclude = ('slug', 'conteudo_html')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].required = False  # Permite salvar sem preencher manualmente

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.cleaned_data.get('arquivo_word'):
            docx_file = self.cleaned_data['arquivo_word']
            html, titulo_detectado, autor_detectado = docx_para_html(docx_file)
            instance.conteudo_html = html

            titulo_base = titulo_detectado or instance.titulo or 'Título não definido'
            titulo_numerado = self.gerar_titulo_numerado(titulo_base)
            instance.titulo = titulo_numerado
            instance.slug = gerar_slug(titulo_numerado)

            if autor_detectado:
                from .models import Autor
                autor_obj, _ = Autor.objects.get_or_create(nome=autor_detectado)
                instance.autor = autor_obj

        if commit:
            instance.save()
        return instance

    @staticmethod
    def gerar_titulo_numerado(titulo_base):
        from .models import Artigo  # importação local para evitar import circular
        artigos_similares = Artigo.objects.filter(titulo__startswith=titulo_base).order_by('id')
        total = artigos_similares.count() + 1  # inclui o atual

        for i, artigo in enumerate(artigos_similares, start=1):
            novo_titulo = f"{titulo_base} ({i} de {total})"
            if artigo.titulo != novo_titulo:
                artigo.titulo = novo_titulo
                artigo.slug = gerar_slug(novo_titulo)
                artigo.save()

        return f"{titulo_base} ({total} de {total})"
