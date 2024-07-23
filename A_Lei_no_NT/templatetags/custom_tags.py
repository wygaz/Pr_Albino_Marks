from django import template
from A_Lei_no_NT.models import Artigo

register = template.Library()

@register.simple_tag
def get_artigos(order='ordem'):
    return Artigo.objects.all().order_by(order)
