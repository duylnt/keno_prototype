from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import display

from .models import (
    CommissionLedger,
    ExperienceCode,
    OwnerWallet,
    PayoutRequest,
    PosLocation,
    WalletTransaction,
)
from .services import approve_payout, reject_payout


@admin.register(PosLocation)
class PosLocationAdmin(ModelAdmin):
    list_display = ("name", "city", "district", "owner", "active_badge")
    list_filter = ("city", "is_active")
    search_fields = ("name", "address", "district", "city", "owner__username")
    raw_id_fields = ("owner",)

    @display(description=_("Hoạt động"), boolean=True)
    def active_badge(self, obj):
        return obj.is_active


@admin.register(ExperienceCode)
class ExperienceCodeAdmin(ModelAdmin):
    list_display = ("code", "created_at", "expires_at", "redeemed_at", "pos", "pos_name")
    list_filter = ("pos", ("redeemed_at", RangeDateFilter))
    search_fields = ("code", "pos_name")
    readonly_fields = ("created_at",)
    raw_id_fields = ("pos",)


@admin.register(CommissionLedger)
class CommissionLedgerAdmin(ModelAdmin):
    list_display = ("created_at", "pos", "owner", "amount_vnd", "points", "status_badge")
    list_filter = ("status", "pos", ("created_at", RangeDateFilter))
    search_fields = ("experience_code__code", "pos__name", "owner__username")
    raw_id_fields = ("experience_code", "pos", "owner")

    @display(
        description=_("Trạng thái"),
        label={
            CommissionLedger.STATUS_AVAILABLE: "success",
            CommissionLedger.STATUS_PENDING: "warning",
            CommissionLedger.STATUS_PAID: "info",
        },
    )
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()


@admin.register(OwnerWallet)
class OwnerWalletAdmin(ModelAdmin):
    list_display = ("user", "points_balance", "updated_at")
    search_fields = ("user__username",)
    raw_id_fields = ("user",)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(ModelAdmin):
    list_display = ("created_at", "wallet", "kind", "points", "amount_vnd", "note")
    list_filter = ("kind", ("created_at", RangeDateFilter))
    search_fields = ("wallet__user__username", "note")
    raw_id_fields = ("wallet", "ledger", "payout")


@admin.register(PayoutRequest)
class PayoutRequestAdmin(ModelAdmin):
    list_display = ("created_at", "owner", "points", "amount_vnd", "status_badge", "reviewed_at")
    list_filter = ("status", ("created_at", RangeDateFilter))
    search_fields = ("owner__username",)
    raw_id_fields = ("owner",)
    actions = ("approve_selected", "reject_selected")
    readonly_fields = ("created_at", "reviewed_at")

    @display(
        description=_("Trạng thái"),
        label={
            PayoutRequest.STATUS_PENDING: "warning",
            PayoutRequest.STATUS_APPROVED: "success",
            PayoutRequest.STATUS_REJECTED: "danger",
        },
    )
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()

    @admin.action(description=_("Duyệt quy đổi (mô phỏng, không chuyển khoản)"))
    def approve_selected(self, request, queryset):
        n = 0
        for obj in queryset.filter(status=PayoutRequest.STATUS_PENDING):
            approve_payout(obj)
            n += 1
        self.message_user(request, f"Đã duyệt {n} yêu cầu (mô phỏng).")

    @admin.action(description=_("Từ chối và hoàn điểm"))
    def reject_selected(self, request, queryset):
        n = 0
        for obj in queryset.filter(status=PayoutRequest.STATUS_PENDING):
            reject_payout(obj)
            n += 1
        self.message_user(request, f"Đã từ chối {n} yêu cầu.")
