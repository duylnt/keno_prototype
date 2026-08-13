from django import template
from django.utils.html import format_html

register = template.Library()

DONG = "₫"


def format_vnd_amount(value) -> str:
    """Vietnamese grouping: 5.000 — never US commas."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = 0
    sign = "−" if n < 0 else ""
    grouped = f"{abs(n):,}".replace(",", ".")
    return f"{sign}{grouped}"


@register.filter(name="vnd")
def vnd(value):
    """Render VND as 5.000 ₫ with a baseline-aligned, unbreakable symbol."""
    return format_html(
        '<span class="vnd money"><span class="vnd-num">{}</span>\u00a0<span class="vnd-sym">{}</span></span>',
        format_vnd_amount(value),
        DONG,
    )
