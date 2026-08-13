from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import Banner, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    fieldsets = (
        (_("Thương hiệu"), {"fields": ("site_name", "tagline", "support_note")}),
        (
            _("Cộng đồng"),
            {
                "fields": (
                    "facebook_group_url",
                    "facebook_page_url",
                    "facebook_app_id",
                    "facebook_comments_url",
                    "facebook_group_name",
                    "community_cta_label",
                )
            },
        ),
        (_("Chuyển đổi offline"), {"fields": ("pos_cta_label", "zalo_group_url")}),
        (_("Theo dõi"), {"fields": ("ga4_measurement_id", "gtm_container_id")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    list_display = ("title", "placement_badge", "is_active", "sort_order")
    list_filter = ("placement", "is_active")
    list_editable = ("sort_order",)
    search_fields = ("title", "subtitle")

    @display(description=_("Vị trí"), label=True)
    def placement_badge(self, obj):
        return obj.get_placement_display()
