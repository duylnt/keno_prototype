from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import display

from .models import Draw


@admin.register(Draw)
class DrawAdmin(ModelAdmin):
    list_display = (
        "period_code",
        "drawn_at",
        "numbers_preview",
        "size_badge",
        "parity_badge",
        "total",
        "sim_badge",
    )
    list_filter = (
        ("drawn_at", RangeDateFilter),
        "size",
        "parity",
        "is_simulated",
        "draw_date",
    )
    search_fields = ("period_code",)
    readonly_fields = ("created_at",)
    date_hierarchy = "draw_date"
    ordering = ("-drawn_at",)
    list_per_page = 50

    @display(description=_("20 số"))
    def numbers_preview(self, obj):
        return " ".join(f"{n:02d}" for n in (obj.numbers_sorted or [])[:20])

    @display(description=_("Lớn/Nhỏ"), label={
        Draw.SIZE_BIG: "success",
        Draw.SIZE_SMALL: "info",
    })
    def size_badge(self, obj):
        return obj.size, obj.size_label

    @display(description=_("Chẵn/Lẻ"), label=True)
    def parity_badge(self, obj):
        return obj.parity_label

    @display(description=_("Mô phỏng"), boolean=True)
    def sim_badge(self, obj):
        return obj.is_simulated
