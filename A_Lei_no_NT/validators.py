# A_Lei_no_NT/validators.py
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

def validate_size(max_mb: int):
    def _v(f):
        if f.size > max_mb * 1024 * 1024:
            raise ValidationError(f"Tamanho máximo permitido: {max_mb} MB.")
    return _v

def validate_docx_mime(f):
    # 1) Pelo content-type do upload (nem sempre confiável, mas ajuda)
    ct = getattr(f, "content_type", None)
    if ct and ct not in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/zip",  # alguns servidores rotulam .docx como zip
    ):
        raise ValidationError("Envie um arquivo .docx válido.")

    # 2) Sniff do conteúdo (opcional, mais robusto)
    try:
        import magic  # pip install python-magic-bin (no Windows)
        head = f.read(2048)
        f.seek(0)
        mime = magic.from_buffer(head, mime=True)
        if mime not in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip"):
            raise ValidationError("O arquivo não parece ser um .docx válido.")
    except Exception:
        # Se não tiver magic instalado, ignore; a verificação de extensão já protege
        pass

def validate_pdf_mime(f):
    ct = getattr(f, "content_type", None)
    if ct and ct != "application/pdf":
        raise ValidationError("Envie um PDF válido.")
    try:
        import magic
        head = f.read(2048); f.seek(0)
        if magic.from_buffer(head, mime=True) != "application/pdf":
            raise ValidationError("O arquivo enviado não é um PDF válido.")
    except Exception:
        pass
