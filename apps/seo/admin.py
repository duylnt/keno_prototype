from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import BrokenLink, CoreWebVitalsNote, ResearchUrl, SeoRedirect, SeoStatus
from .views_admin import SeoResearchView, SeoToolboxView, SeoWriterView


@admin.register(SeoRedirect)
class SeoRedirectAdmin(ModelAdmin):
    list_display = ("from_path", "to_path", "permanent_badge", "is_active", "hit_count")
    list_filter = ("is_permanent", "is_active")
    search_fields = ("from_path", "to_path", "note")

    @display(description=_("301"), boolean=True)
    def permanent_badge(self, obj):
        return obj.is_permanent


@admin.register(ResearchUrl)
class ResearchUrlAdmin(ModelAdmin):
    list_display = ("title", "product_hint", "status", "word_count", "fetched_at")
    list_filter = ("product_hint", "status")
    search_fields = ("url", "title", "keyword_hints", "excerpt")
    readonly_fields = (
        "url",
        "title",
        "meta_description",
        "canonical",
        "headings",
        "outline",
        "excerpt",
        "word_count",
        "keyword_hints",
        "schema_types",
        "published_hint",
        "http_status",
        "robots_allowed",
        "status",
        "error_message",
        "fetched_at",
    )


@admin.register(BrokenLink)
class BrokenLinkAdmin(ModelAdmin):
    list_display = ("source_path", "target_url", "status_code", "checked_at")
    list_filter = ("status_code",)
    search_fields = ("source_path", "target_url")
    readonly_fields = ("source_path", "target_url", "status_code", "is_internal", "checked_at")


@admin.register(CoreWebVitalsNote)
class CoreWebVitalsNoteAdmin(ModelAdmin):
    list_display = ("date", "lcp_note", "inp_note", "cls_note")


@admin.register(SeoStatus)
class SeoStatusAdmin(ModelAdmin):
    list_display = ("sitemap_generated_at", "linkcheck_at", "linkcheck_broken", "research_at")

    def has_add_permission(self, request):
        return not SeoStatus.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


def _register_custom_admin_urls():
    original = admin.site.get_urls

    def get_urls():
        extra = [
            path(
                "seo/cong-cu/",
                admin.site.admin_view(SeoToolboxView.as_view()),
                name="seo_toolbox",
            ),
            path(
                "seo/phan-tich-url/",
                admin.site.admin_view(SeoResearchView.as_view()),
                name="seo_research",
            ),
            path(
                "seo/viet-bai/",
                admin.site.admin_view(SeoWriterView.as_view()),
                name="seo_writer",
            ),
        ]
        return extra + original()

    admin.site.get_urls = get_urls


_register_custom_admin_urls()
