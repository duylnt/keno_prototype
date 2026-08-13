from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display

from apps.community.facebook import mask_token

from .models import Banner, SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = "__all__"
        widgets = {
            "facebook_page_access_token": forms.PasswordInput(
                render_value=False,
                attrs={"autocomplete": "new-password", "placeholder": "••••••••"},
            ),
            "facebook_moderation_roles": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        token_field = self.fields["facebook_page_access_token"]
        token_field.required = False
        token_field.help_text = "Để trống nếu không đổi. Token không bao giờ hiện đầy đủ."
        current = (self.instance.facebook_page_access_token or "").strip() if self.instance.pk else ""
        if current:
            token_field.help_text = (
                f"Đang dùng: {mask_token(current)}. Nhập token mới để thay — để trống giữ nguyên."
            )

    def clean_facebook_page_access_token(self):
        value = (self.cleaned_data.get("facebook_page_access_token") or "").strip()
        if not value and self.instance.pk:
            return self.instance.facebook_page_access_token
        return value


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    form = SiteSettingsForm
    compressed_fields = True
    warn_unsaved_form = True
    readonly_fields = ("fanpage_tools",)
    fieldsets = (
        (_("Thương hiệu"), {"fields": ("site_name", "tagline", "support_note")}),
        (
            _("Fanpage Facebook"),
            {
                "fields": (
                    "facebook_page_url",
                    "facebook_page_id",
                    "facebook_app_id",
                    "facebook_page_access_token",
                    "facebook_moderation_roles",
                    "fanpage_tools",
                )
            },
        ),
        (
            _("Cộng đồng"),
            {
                "fields": (
                    "facebook_group_url",
                    "facebook_comments_url",
                    "facebook_group_name",
                    "community_cta_label",
                )
            },
        ),
        (
            _("Hoa hồng điểm bán"),
            {
                "fields": (
                    "o2o_commission_type",
                    "o2o_commission_rate",
                    "o2o_commission_base_vnd",
                    "wallet_vnd_per_point",
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

    def fanpage_tools(self, obj):
        url = reverse("admin:community_fanpage")
        return format_html('<a href="{}">Kiểm duyệt Fanpage</a> · đồng bộ Graph API tại đó', url)

    fanpage_tools.short_description = "Công cụ Fanpage"


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    list_display = ("title", "placement_badge", "is_active", "sort_order")
    list_filter = ("placement", "is_active")
    list_editable = ("sort_order",)
    search_fields = ("title", "subtitle")

    @display(description=_("Vị trí"), label=True)
    def placement_badge(self, obj):
        return obj.get_placement_display()
