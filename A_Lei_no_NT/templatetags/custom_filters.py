from django import template
from unidecode import unidecode
import re

register = template.Library()

@register.filter(name='replace_spaces')
def replace_spaces(value):
    # Remove acentos e caracteres especiais e substitui espaços por underscores
    value_unaccented = unidecode(value)
    value_cleaned = re.sub(r'[^a-zA-Z0-9_]+', '', value_unaccented.replace(" ", "_"))
    return value_cleaned.upper()
