# em templatetags/form_extras.py
from django import template
register = template.Library()

@register.filter
def add_class(field, css):
    return field.as_widget(attrs={**field.field.widget.attrs, "class": css})

@register.filter
def attr(field, arg):
    k, v = arg.split(":", 1)
    return field.as_widget(attrs={**field.field.widget.attrs, k: v})
