from django import forms
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from .models import Artigo, Autor
from .utils import docx_para_html, gerar_slug
from A_Lei_no_NT.utils_storage import open_file
# imports (topo do forms.py)
from django.utils.safestring import mark_safe
import os

class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        # >>> ORDEM dos campos no formulário <<<
        fields = (
            "titulo",
            "arquivo_pdf",    # 1º
            "arquivo_word",   # 2º
            "imagem_capa",    # 3º
            "publicado_em",
            "ordem",
            "visivel",
            "autor",
            "area",
            # 'conteudo_html' fica fora do form (preenchido via DOCX)
            # 'slug' também fica fora (gerado automaticamente)
        )
        labels = {
            "arquivo_pdf":  "Arquivo PDF",
            "arquivo_word": "Arquivo DOCX",
            "imagem_capa":  "Imagem (PNG/JPG/WEBP)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos opcionais para permitir qualquer combinação (pdf/word/imagem)
        self.fields["titulo"].required = False
        self.fields["arquivo_pdf"].required = False
        self.fields["arquivo_word"].required = False
        self.fields["imagem_capa"].required = False

        # Aceites nos inputs
        self.fields["arquivo_pdf"].widget.attrs.update({
            "accept": "application/pdf"
        })
        self.fields["arquivo_word"].widget.attrs.update({
            "accept": ".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        })
        self.fields["imagem_capa"].widget.attrs.update({
            "accept": "image/png,image/jpeg,image/webp,image/*"
        })

    # --- Validações leves de extensão ---
    def clean_arquivo_pdf(self):
        f = self.cleaned_data.get("arquivo_pdf")
        if f and not f.name.lower().endswith(".pdf"):
            raise ValidationError("Apenas arquivos .pdf são permitidos.")
        return f

    def clean_arquivo_word(self):
        f = self.cleaned_data.get("arquivo_word")
        if f and not f.name.lower().endswith(".docx"):
            raise ValidationError("Apenas arquivos .docx são permitidos.")
        return f

    def clean_imagem_capa(self):
        img = self.cleaned_data.get("imagem_capa")
        if img:
            ext = os.path.splitext(img.name)[1].lower()
            if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                raise ValidationError("Use PNG, JPG, JPEG ou WEBP.")
        return img

    def save(self, commit=True):
        """
        Mantém tua lógica:
        - Se DOCX, converte para HTML, detecta título/autor e numera título.
        - Garante slug mesmo sem DOCX (fallback).
        - Renomeio de imagem preservado na função auxiliar.
        """
        instance = super().save(commit=False)

        if self.cleaned_data.get("arquivo_word"):
            docx_file = self.cleaned_data["arquivo_word"]
            html, titulo_detectado, autor_detectado = docx_para_html(docx_file)
            instance.conteudo_html = html

            titulo_base = titulo_detectado or instance.titulo or "Título não definido"
            titulo_numerado = self.gerar_titulo_numerado(titulo_base)
            instance.titulo = titulo_numerado

            if not instance.slug:
                instance.slug = gerar_slug(titulo_numerado)

            if autor_detectado:
                autor_obj, _ = Autor.objects.get_or_create(nome=autor_detectado)
                instance.autor = autor_obj
        else:
            # Se a view não setou, garante o slug aqui
            if not instance.slug:
                instance.slug = gerar_slug(instance.titulo or "Artigo Sem Título")

        if commit:
            instance.save()
            # se tiver M2M
            try:
                self.save_m2m()
            except Exception:
                pass
        return instance

    @staticmethod
    def gerar_titulo_numerado(titulo_base):
        """
        Mantém tua numeração + renomeio de imagem (S3-safe).
        """
        from .models import Artigo  # evita import circular
        artigos_similares = Artigo.objects.filter(
            titulo__startswith=titulo_base
        ).order_by("id")
        total = artigos_similares.count() + 1

        for i, artigo in enumerate(artigos_similares, start=1):
            novo_titulo = f"{titulo_base} ({i} de {total})"
            if artigo.titulo != novo_titulo:
                artigo.titulo = novo_titulo
                artigo.slug = gerar_slug(novo_titulo)
                artigo.save(update_fields=["titulo", "slug"])

            # Renomear a imagem associada, se existir (S3-safe)
            if artigo.imagem_capa:
                old_name = artigo.imagem_capa.name  # ex: 'imagens/artigos/abc.jpg'
                ext = os.path.splitext(old_name)[1]
                novo_nome = f"{artigo.slug}{ext}"
                novo_path = f"imagens/artigos/{novo_nome}"

                if os.path.basename(old_name) != novo_nome:
                    if default_storage.exists(novo_path):
                        default_storage.delete(novo_path)
                    try:
                        with open_file(old_name, "rb") as src:
                            default_storage.save(novo_path, src)
                        if default_storage.exists(old_name):
                            default_storage.delete(old_name)
                        artigo.imagem_capa.name = novo_path
                        artigo.save(update_fields=["imagem_capa"])
                        print(f"🔁 Imagem renomeada: {novo_path}")
                    except Exception as e:
                        print(f"⚠️ Erro ao renomear imagem de '{artigo.titulo}': {e}")

        return f"{titulo_base} ({total} de {total})"
