"""Keno URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import index as sitemap_index
from django.contrib.sitemaps.views import sitemap as sitemap_section
from django.urls import include, path

from apps.seo.sitemaps import SITEMAPS
from apps.seo.views import _mark_sitemap


def sitemap_index_view(request):
    _mark_sitemap()
    return sitemap_index(request, sitemaps=SITEMAPS)


urlpatterns = [
    path("cms/", admin.site.urls),
    path("sitemap.xml", sitemap_index_view, name="sitemap"),
    path(
        "sitemap-<section>.xml",
        sitemap_section,
        {"sitemaps": SITEMAPS},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", include("apps.seo.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.results.urls")),
    path("", include("apps.content.urls")),
    path("", include("apps.community.urls")),
    path("", include("apps.locations.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
]

handler404 = "apps.seo.views.page_not_found"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
