from django import template
from django.utils.html import mark_safe
from django.forms import BoundField
import re


register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"class": css_class})
    return field

@register.filter(name='highlight')
def highlight(text, query):
    if not query:
        return text
    words = re.split(r'\s+', query)
    for word in words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        text = pattern.sub(
            lambda m: f'<mark class="highlight">{m.group(0)}</mark>', 
            str(text)
        )
    return mark_safe(text)