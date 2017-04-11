from django import template

register = template.Library()


@register.filter
def percentage(value):
    """Converts a fraction to a percentage."""
    return '{:.0f}'.format(value * 100)
