from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from apps.content.models import Article, StaticPage
from apps.locations.models import PosLocation
from apps.results.models import Draw

from .utils import site_protocol


class _ProtoMixin:
    def get_protocol(self, protocol=None):
        return site_protocol()


class StaticViewSitemap(_ProtoMixin, Sitemap):
    changefreq = "hourly"
    priority = 0.9

    def items(self):
        return [
            "core:home",
            "results:live",
            "results:today",
            "results:history",
            "results:stats",
            "results:stats_size",
            "results:stats_parity",
            "results:check_ticket",
            "results:simulator",
            "locations:finder",
            "community:hub",
            "community:guidelines",
            "content:how_to_play",
            "content:info_hub",
            "content:article_list",
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        if item.startswith("results:"):
            draw = Draw.objects.order_by("-drawn_at").first()
            return draw.drawn_at if draw else timezone.now()
        article = Article.objects.filter(is_published=True).order_by("-updated_at").first()
        return article.updated_at if article else timezone.now()


class ArticleSitemap(_ProtoMixin, Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Article.objects.filter(is_published=True, robots_noindex=False)

    def lastmod(self, obj):
        return obj.updated_at


class StaticPageSitemap(_ProtoMixin, Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return StaticPage.objects.filter(is_published=True, robots_noindex=False)

    def lastmod(self, obj):
        return obj.updated_at


class LocationSitemap(_ProtoMixin, Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return PosLocation.objects.filter(is_active=True)


SITEMAPS = {
    "pages": StaticViewSitemap,
    "articles": ArticleSitemap,
    "info": StaticPageSitemap,
    "locations": LocationSitemap,
}
