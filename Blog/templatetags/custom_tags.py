from django import template
\l Blog.models import Artigo

register = template.Library()

@register.simple_tag
def get_artigos(order='ordem'):
    return Artigo.objects.all().order_by(order)
