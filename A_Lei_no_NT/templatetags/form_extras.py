# A_Lei_no_NT/templatetags/form_extras.py
from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name="add_class")
def add_class(field, css):
    """
    Adiciona classes CSS a um BoundField. Se não for BoundField, retorna o valor original.
    """
    if isinstance(field, BoundField):
        attrs = dict(getattr(field.field.widget, "attrs", {}))
        attrs["class"] = (attrs.get("class", "") + " " + (css or "")).strip()
        return field.as_widget(attrs=attrs)
    return field  # tolerante a strings/None

@register.filter(name="attr")
def attr(field, arg):
    """
    Define um atributo (ex.: {{ form.titulo|attr:"placeholder: Digite o título" }}).
    Só atua em BoundField; se não for, retorna o valor original.
    """
    if not isinstance(field, BoundField):
        return field
    if not isinstance(arg, str) or ":" not in arg:
        return field
    k, v = (s.strip() for s in arg.split(":", 1))
    attrs = dict(getattr(field.field.widget, "attrs", {}))
    attrs[k] = v
    return field.as_widget(attrs=attrs)
