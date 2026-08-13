from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import display

from .models import Article, ArticleCategory, ArticleFAQ, StaticPage


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(ModelAdmin):
    list_display = ("name", "slug", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ArticleFAQInline(TabularInline):
    model = ArticleFAQ
    extra = 1
    tab = True
    verbose_name = _("FAQ")
    verbose_name_plural = _("FAQ")


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        widgets = {
            "body": WysiwygWidget(),
            "excerpt": forms.Textarea(attrs={"rows": 3}),
            "key_takeaways": forms.Textarea(attrs={"rows": 4}),
        }


@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    form = ArticleAdminForm
    inlines = (ArticleFAQInline,)
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ("title", "category", "published_badge", "index_badge", "published_at")
    list_filter = ("category", "is_published", "robots_noindex", ("published_at", RangeDateFilter))
    search_fields = ("title", "excerpt", "body", "slug", "focus_keyword")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    readonly_fields = ("seo_preview_panel", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "category",
                    "title",
                    "slug",
                    "excerpt",
                    "body",
                    "cover",
                    "cover_alt",
                    "key_takeaways",
                )
            },
        ),
        (
            _("SEO"),
            {
                "fields": (
                    "focus_keyword",
                    "seo_title",
                    "seo_description",
                    "seo_preview_panel",
                )
            },
        ),
        (
            _("SEO nâng cao"),
            {
                "classes": ("collapse",),
                "fields": (
                    "canonical_url",
                    "og_image",
                    "robots_noindex",
                    "author_name",
                ),
            },
        ),
        (_("Xuất bản"), {"fields": ("is_published", "published_at", "updated_at")}),
    )

    class Media:
        js = ("js/seo-editor.js",)
        css = {"all": ("css/seo-editor.css",)}

    @display(description=_("Xuất bản"), boolean=True)
    def published_badge(self, obj):
        return obj.is_published

    @display(description=_("Index"), boolean=True)
    def index_badge(self, obj):
        return obj.is_published and not obj.robots_noindex

    def seo_preview_panel(self, obj):
        return format_html(
            '<div id="keno-seo-panel" class="keno-seo-panel" data-path="/bai-viet/{}/">'
            '<p class="keno-seo-label">Xem trước Google</p>'
            '<div class="keno-serp">'
            '<div class="keno-serp-url" id="seo-serp-url"></div>'
            '<div class="keno-serp-title" id="seo-serp-title"></div>'
            '<div class="keno-serp-desc" id="seo-serp-desc"></div>'
            "</div>"
            '<p class="keno-seo-label">Checklist</p>'
            '<ul class="keno-seo-checks" id="seo-checks"></ul>'
            "</div>",
            obj.slug if obj and obj.pk else "slug",
        )

    seo_preview_panel.short_description = _("Xem trước & checklist")


class StaticPageAdminForm(forms.ModelForm):
    class Meta:
        model = StaticPage
        fields = "__all__"
        widgets = {"body": WysiwygWidget(), "excerpt": forms.Textarea(attrs={"rows": 3})}


@admin.register(StaticPage)
class StaticPageAdmin(ModelAdmin):
    form = StaticPageAdminForm
    list_display = ("title", "slug", "is_published", "robots_noindex", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "body")
    fieldsets = (
        (None, {"fields": ("title", "slug", "excerpt", "body", "is_published")}),
        (
            _("SEO"),
            {
                "fields": ("seo_title", "seo_description", "canonical_url", "og_image", "robots_noindex"),
            },
        ),
    )
