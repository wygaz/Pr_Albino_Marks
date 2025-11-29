
def gerar_slug(titulo):
    from .models import Artigo

    if not titulo or not titulo.strip():
        titulo = "Artigo Sem Título"

    slug_base = slugify(unidecode(titulo))
    if not slug_base:
        slug_base = f"artigo-{uuid4().hex[:6]}"

    slug = slug_base
    contador = 2
    while Artigo.objects.filter(slug=slug).exists():
        slug = f"{slug_base}-{contador}"
        contador += 1

    return slug
