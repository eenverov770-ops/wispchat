from django import template

register = template.Library()

@register.filter
def splitlines(value):
    """Разбивает строку по переносам строк и возвращает список"""
    if not value:
        return []
    return value.split('\n')