from __future__ import annotations

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.content.models import Article, StaticPage
from apps.core.models import SiteSettings

from .models import BrokenLink, CoreWebVitalsNote, ResearchUrl, SeoRedirect, SeoStatus
from .sample_market import SUGGESTED_GAP_TOPICS
from .utils import site_origin
from .writer import api_configured


def coverage_gaps() -> list[dict]:
    titles = " ".join(
        Article.objects.filter(is_published=True).values_list("title", flat=True)
    ).lower()
    keywords = " ".join(
        f"{kw} {slug}"
        for kw, slug in Article.objects.filter(is_published=True).values_list("focus_keyword", "slug")
    ).lower()
    blob = f"{titles} {keywords}"
    gaps: list[dict] = []
    for row in ResearchUrl.objects.all()[:80]:
        missing = []
        for kw in row.keyword_list:
            token = kw.lower()
            if token and token not in blob:
                missing.append(kw)
        if missing or row.product_hint != "keno":
            gaps.append(
                {
                    "source": row,
                    "missing_keywords": missing,
                    "topic": row.title or row.url,
                    "product": row.get_product_hint_display(),
                }
            )
    for topic in SUGGESTED_GAP_TOPICS:
        if topic.lower() not in blob and not any(topic.lower() in (g["topic"] or "").lower() for g in gaps):
            gaps.append(
                {
                    "source": None,
                    "missing_keywords": [topic],
                    "topic": topic,
                    "product": "Gợi ý",
                }
            )
    return gaps[:20]


def indexing_overview() -> dict:
    published = Article.objects.filter(is_published=True)
    site = SiteSettings.load()
    status = SeoStatus.load()
    cwv = CoreWebVitalsNote.objects.order_by("-date").first()
    return {
        "articles_published": published.count(),
        "articles_indexed": published.filter(robots_noindex=False).count(),
        "articles_noindex": Article.objects.filter(Q(robots_noindex=True) | Q(is_published=False)).count(),
        "articles_draft": Article.objects.filter(is_published=False).count(),
        "pages_published": StaticPage.objects.filter(is_published=True, robots_noindex=False).count(),
        "redirects": SeoRedirect.objects.filter(is_active=True).count(),
        "research_rows": ResearchUrl.objects.count(),
        "broken_links": BrokenLink.objects.count(),
        "ga4_id": site.ga4_measurement_id or settings.GA4_MEASUREMENT_ID or "(chưa cấu hình)",
        "gtm_id": site.gtm_container_id or settings.GTM_CONTAINER_ID or "(chưa cấu hình)",
        "gsc_site": settings.GSC_SITE_URL,
        "site_url": site_origin(),
        "sitemap_generated_at": status.sitemap_generated_at,
        "linkcheck_at": status.linkcheck_at,
        "linkcheck_ok": status.linkcheck_ok,
        "linkcheck_broken": status.linkcheck_broken,
        "research_at": status.research_at,
        "api_configured": api_configured(),
        "cwv": cwv,
        "now": timezone.now(),
    }
