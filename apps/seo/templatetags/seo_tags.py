from django import template
from django.utils.safestring import mark_safe

from apps.seo.schema import build_graph

register = template.Library()


@register.simple_tag(takes_context=True)
def jsonld_script(context):
    import json

    graph = build_graph(context.flatten() if hasattr(context, "flatten") else dict(context))
    payload = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')
