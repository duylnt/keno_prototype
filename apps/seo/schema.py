"""JSON-LD graph for public pages. Do not impersonate Vietlott."""

from __future__ import annotations

from django.utils.html import strip_tags

from .utils import absolute_url, site_origin


def _org(site) -> dict:
    return {
        "@type": "Organization",
        "@id": f"{site_origin()}/#organization",
        "name": site.site_name,
        "url": site_origin() + "/",
        "description": (
            f"{site.tagline}. Cổng cộng đồng tra cứu Keno — không phải website "
            "chính thức của Vietlott và không bán vé trực tuyến."
        ),
        "inLanguage": "vi-VN",
    }


def _website(site) -> dict:
    return {
        "@type": "WebSite",
        "@id": f"{site_origin()}/#website",
        "name": site.site_name,
        "url": site_origin() + "/",
        "description": site.tagline,
        "inLanguage": "vi-VN",
        "publisher": {"@id": f"{site_origin()}/#organization"},
    }


def _webpage(*, name: str, description: str, url: str, extra: dict | None = None) -> dict:
    node = {
        "@type": "WebPage",
        "@id": f"{url}#webpage",
        "url": url,
        "name": name,
        "description": description,
        "inLanguage": "vi-VN",
        "isPartOf": {"@id": f"{site_origin()}/#website"},
        "about": {"@id": f"{site_origin()}/#organization"},
    }
    if extra:
        node.update(extra)
    return node


def breadcrumbs(items: list[tuple[str, str]]) -> dict:
    """items: list of (name, url)."""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "name": name,
                "item": absolute_url(url),
            }
            for i, (name, url) in enumerate(items, start=1)
        ],
    }


def article_node(article, url: str) -> dict:
    node = {
        "@type": "Article",
        "@id": f"{url}#article",
        "headline": article.title,
        "description": article.meta_description,
        "datePublished": article.published_at.isoformat() if article.published_at else None,
        "dateModified": article.updated_at.isoformat() if article.updated_at else None,
        "inLanguage": "vi-VN",
        "mainEntityOfPage": {"@id": f"{url}#webpage"},
        "author": {
            "@type": "Person",
            "name": getattr(article, "author_name", None) or "Ban biên tập Keno",
        },
        "publisher": {"@id": f"{site_origin()}/#organization"},
    }
    if getattr(article, "focus_keyword", ""):
        node["keywords"] = article.focus_keyword
    image = article.og_image_url
    if image:
        node["image"] = image
    return {k: v for k, v in node.items() if v is not None}


def faq_node(faqs, page_url: str) -> dict | None:
    rows = [f for f in faqs if getattr(f, "question", "") and getattr(f, "answer", "")]
    if not rows:
        return None
    return {
        "@type": "FAQPage",
        "@id": f"{page_url}#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f.question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": strip_tags(f.answer),
                },
            }
            for f in rows
        ],
    }


def howto_node(name: str, description: str, steps: list[dict], url: str) -> dict:
    return {
        "@type": "HowTo",
        "@id": f"{url}#howto",
        "name": name,
        "description": description,
        "inLanguage": "vi-VN",
        "step": [
            {
                "@type": "HowToStep",
                "position": i,
                "name": step["name"],
                "text": step["text"],
            }
            for i, step in enumerate(steps, start=1)
        ],
    }


def local_business(loc, url: str) -> dict:
    return {
        "@type": "LocalBusiness",
        "name": loc.name,
        "description": (
            f"Điểm bán Keno cộng đồng liệt kê — {loc.address}. "
            "Không phải trang chính thức Vietlott."
        ),
        "url": url,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": loc.address,
            "addressLocality": loc.district or loc.city,
            "addressRegion": loc.city,
            "addressCountry": "VN",
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": str(loc.latitude),
            "longitude": str(loc.longitude),
        },
        "telephone": loc.phone or None,
        "openingHours": loc.opening_hours or None,
    }


def build_graph(context: dict) -> dict:
    site = context.get("site_settings")
    if site is None:
        from apps.core.models import SiteSettings

        site = SiteSettings.load()
    request = context.get("request")
    canonical = context.get("canonical_url") or (absolute_url(request.path) if request else site_origin() + "/")
    title = context.get("page_title") or site.site_name
    description = context.get("meta_description") or site.tagline
    graph: list[dict] = [_org(site), _website(site), _webpage(name=title, description=description, url=canonical)]

    crumbs = context.get("breadcrumbs")
    if crumbs:
        graph.append(breadcrumbs(crumbs))

    article = context.get("article")
    path = request.path if request else ""
    if article and getattr(article, "pk", None) and path.startswith("/bai-viet/"):
        graph.append(article_node(article, canonical))
        faqs = context.get("article_faqs")
        if faqs is None:
            faqs = list(getattr(article, "faqs", []).all()) if hasattr(article, "faqs") else []
        faq = faq_node(faqs, canonical)
        if faq:
            graph.append(faq)

    faq_items = context.get("faq_items")
    if faq_items and not any(n.get("@type") == "FAQPage" for n in graph):
        class _F:
            def __init__(self, q, a):
                self.question, self.answer = q, a

        faq = faq_node([_F(x["q"], x["a"]) for x in faq_items], canonical)
        if faq:
            graph.append(faq)

    howto_steps = context.get("howto_steps")
    if howto_steps:
        graph.append(
            howto_node(
                context.get("howto_name") or title,
                description,
                howto_steps,
                canonical,
            )
        )

    loc = context.get("loc")
    if loc is not None and getattr(loc, "address", None):
        node = local_business(loc, canonical)
        graph.append({k: v for k, v in node.items() if v is not None})

    return {"@context": "https://schema.org", "@graph": graph}
