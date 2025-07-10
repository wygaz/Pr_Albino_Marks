from django import forms
from .models import Artigo
from .utils import docx_para_html, gerar_slug
from django.db.models import Count
import os

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        exclude = ('slug', 'conteudo_html')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].required = False  # Permite salvar sem preencher manualmente

        # 🔒 Limitar seleção de arquivos a .docx no navegador
        self.fields['arquivo_word'].widget.attrs.update({
            'accept': '.docx'
        })

    def clean_arquivo_word(self):
        arquivo = self.cleaned_data.get('arquivo_word')
        if arquivo and not arquivo.name.endswith('.docx'):
            raise forms.ValidationError('Apenas arquivos .docx são permitidos.')
        return arquivo

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

            # Renomear a imagem associada, se existir
            if artigo.imagem_capa:
                from django.conf import settings
                antiga_path = artigo.imagem_capa.path
                ext = os.path.splitext(antiga_path)[1]
                novo_nome = f"{artigo.slug}{ext}"
                novo_path = os.path.join(settings.MEDIA_ROOT, "imagens", "artigos", novo_nome)

                try:
                    os.rename(antiga_path, novo_path)
                    artigo.imagem_capa.name = f"imagens/artigos/{novo_nome}"
                    artigo.save()
                    print(f"🔁 Imagem renomeada com sucesso: {novo_nome}")
                except Exception as e:
                    print(f"⚠️ Erro ao renomear imagem do artigo '{artigo.titulo}': {e}")


        return f"{titulo_base} ({total} de {total})"
