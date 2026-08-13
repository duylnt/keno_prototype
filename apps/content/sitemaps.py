"""Re-export sitemaps from apps.seo for older imports."""

from apps.seo.sitemaps import ArticleSitemap, StaticPageSitemap

__all__ = ["ArticleSitemap", "StaticPageSitemap"]
