from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import ExperienceCode, PosLocation


@admin.register(PosLocation)
class PosLocationAdmin(ModelAdmin):
    list_display = ("name", "city", "district", "address", "active_badge")
    list_filter = ("city", "is_active")
    search_fields = ("name", "address", "district", "city")

    @display(description=_("Hoạt động"), boolean=True)
    def active_badge(self, obj):
        return obj.is_active


@admin.register(ExperienceCode)
class ExperienceCodeAdmin(ModelAdmin):
    list_display = ("code", "created_at", "expires_at", "redeemed_at", "pos_name")
    list_filter = ("pos_name",)
    search_fields = ("code", "pos_name")
    readonly_fields = ("created_at",)
