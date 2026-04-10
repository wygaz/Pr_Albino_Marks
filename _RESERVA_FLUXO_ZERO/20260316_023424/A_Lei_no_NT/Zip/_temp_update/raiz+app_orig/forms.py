# A_Lei_no_NT/forms.py
from django import forms
from django.core.exceptions import ValidationError

from .models import Artigo, Autor
from .utils import docx_para_html, gerar_slug, limpar_numeracao

import os


class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        # >>> ORDEM dos campos no formulário <<<
        fields = (
            "titulo",
            "arquivo_pdf",
            "arquivo_word",
            "imagem_capa",
            "publicado_em",
            "ordem",
            "visivel",
            "autor",
            "area",
            "conteudo_html",  # ✅ agora aparece no admin para correção manual
        )
        labels = {
            "arquivo_pdf":  "Arquivo PDF",
            "arquivo_word": "Arquivo DOCX",
            "imagem_capa":  "Imagem (PNG/JPG/WEBP)",
            "conteudo_html": "Conteúdo (HTML)",
        }
        widgets = {
            "conteudo_html": forms.Textarea(attrs={
                "rows": 28,
                "style": "font-family: ui-monospace, Consolas, monospace; font-size: 12px;",
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos opcionais para permitir qualquer combinação (pdf/word/imagem)
        self.fields["titulo"].required = False
        self.fields["arquivo_pdf"].required = False
        self.fields["arquivo_word"].required = False
        self.fields["imagem_capa"].required = False
        self.fields["conteudo_html"].required = False

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
        if f and hasattr(f, "name") and not f.name.lower().endswith(".docx"):
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
        - Se DOCX NOVO for enviado, converte para HTML e detecta título/autor.
        - Não numera título automaticamente (só limpa numeração indevida).
        - Garante slug mesmo sem DOCX (fallback).
        - Se não houver DOCX novo, NÃO sobrescreve conteudo_html.
        """
        instance = super().save(commit=False)

        # ✅ Só faz conversão se houver upload novo neste POST
        docx_file = self.files.get("arquivo_word")

        if docx_file:
            html, titulo_detectado, autor_detectado = docx_para_html(docx_file)
            instance.conteudo_html = html

            # Base do título vinda do DOCX (ou do próprio instance)
            titulo_base = (titulo_detectado or instance.titulo or "Título não definido").strip()

            # Remove qualquer numeração tipo "1 de 3", "(1/3)", "nº 1", "parte 1", etc.
            titulo_limpo = limpar_numeracao(titulo_base).strip()

            # Grava só o título limpo, sem numeração automática
            instance.titulo = titulo_limpo
            instance.slug = gerar_slug(titulo_limpo)

            if autor_detectado:
                autor_nome = str(autor_detectado).strip()
                if autor_nome:
                    autor_obj, _ = Autor.objects.get_or_create(nome=autor_nome)
                    instance.autor = autor_obj

        else:
            # Se não subiu DOCX novo, mantém o HTML como está (inclusive correções manuais)
            if not instance.slug:
                instance.slug = gerar_slug(instance.titulo or "Artigo Sem Título")

        if commit:
            instance.save()
            try:
                self.save_m2m()
            except Exception:
                pass

        return instance
