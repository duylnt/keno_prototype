"""O2O commission + owner wallet (prototype, no real payouts)."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.core.models import SiteSettings

from .models import (
    CommissionLedger,
    ExperienceCode,
    OwnerWallet,
    PayoutRequest,
    PosLocation,
    WalletTransaction,
)


def commission_amounts(site: SiteSettings | None = None) -> tuple[int, int]:
    site = site or SiteSettings.load()
    rate = float(site.o2o_commission_rate or 0)
    if site.o2o_commission_type == SiteSettings.COMMISSION_PERCENT:
        base = int(site.o2o_commission_base_vnd or 0)
        amount = int(round(base * rate / 100.0))
    else:
        amount = int(round(rate))
    amount = max(amount, 0)
    per_point = int(site.wallet_vnd_per_point or 1) or 1
    points = amount // per_point
    return amount, points


def vnd_per_point(site: SiteSettings | None = None) -> int:
    site = site or SiteSettings.load()
    return int(site.wallet_vnd_per_point or 1) or 1


@transaction.atomic
def credit_o2o_commission(code: ExperienceCode) -> CommissionLedger | None:
    """Idempotent: one ledger row per redeemed code."""
    if not code.redeemed_at:
        return None
    existing = CommissionLedger.objects.filter(experience_code=code).first()
    if existing:
        return existing
    pos = code.pos
    if pos is None and code.pos_name:
        pos = PosLocation.objects.filter(name=code.pos_name).first()
        if pos:
            code.pos = pos
            code.save(update_fields=["pos"])
    if pos is None:
        return None
    site = SiteSettings.load()
    amount, points = commission_amounts(site)
    ledger = CommissionLedger.objects.create(
        experience_code=code,
        pos=pos,
        owner=pos.owner,
        amount_vnd=amount,
        points=points,
        status=CommissionLedger.STATUS_AVAILABLE,
        created_at=code.redeemed_at or timezone.now(),
    )
    if pos.owner_id and points:
        wallet, _ = OwnerWallet.objects.select_for_update().get_or_create(user=pos.owner)
        wallet.points_balance = int(wallet.points_balance) + points
        wallet.save(update_fields=["points_balance", "updated_at"])
        WalletTransaction.objects.create(
            wallet=wallet,
            kind=WalletTransaction.KIND_EARN,
            points=points,
            amount_vnd=amount,
            note="Hoa hồng quét mã O2O",
            ledger=ledger,
        )
    return ledger


@transaction.atomic
def request_payout(user, points: int) -> PayoutRequest:
    site = SiteSettings.load()
    rate = vnd_per_point(site)
    points = int(points)
    if points <= 0:
        raise ValueError("Số điểm phải lớn hơn 0.")
    wallet, _ = OwnerWallet.objects.select_for_update().get_or_create(user=user)
    if wallet.points_balance < points:
        raise ValueError("Không đủ điểm trong ví.")
    amount = points * rate
    wallet.points_balance -= points
    wallet.save(update_fields=["points_balance", "updated_at"])
    payout = PayoutRequest.objects.create(
        owner=user,
        points=points,
        amount_vnd=amount,
        status=PayoutRequest.STATUS_PENDING,
    )
    WalletTransaction.objects.create(
        wallet=wallet,
        kind=WalletTransaction.KIND_PAYOUT,
        points=-points,
        amount_vnd=-amount,
        note="Yêu cầu quy đổi — chờ duyệt",
        payout=payout,
    )
    return payout


@transaction.atomic
def approve_payout(payout: PayoutRequest, staff_note: str = "") -> None:
    if payout.status != PayoutRequest.STATUS_PENDING:
        return
    payout.status = PayoutRequest.STATUS_APPROVED
    payout.reviewed_at = timezone.now()
    payout.staff_note = (staff_note or "Đã duyệt mô phỏng — không chuyển khoản thật.").strip()[:200]
    payout.save(update_fields=["status", "reviewed_at", "staff_note"])
    CommissionLedger.objects.filter(
        owner=payout.owner,
        status=CommissionLedger.STATUS_AVAILABLE,
    ).update(status=CommissionLedger.STATUS_PAID)


@transaction.atomic
def reject_payout(payout: PayoutRequest, staff_note: str = "") -> None:
    if payout.status != PayoutRequest.STATUS_PENDING:
        return
    payout.status = PayoutRequest.STATUS_REJECTED
    payout.reviewed_at = timezone.now()
    payout.staff_note = (staff_note or "Từ chối yêu cầu quy đổi.").strip()[:200]
    payout.save(update_fields=["status", "reviewed_at", "staff_note"])
    wallet, _ = OwnerWallet.objects.select_for_update().get_or_create(user=payout.owner)
    wallet.points_balance = int(wallet.points_balance) + payout.points
    wallet.save(update_fields=["points_balance", "updated_at"])
    WalletTransaction.objects.create(
        wallet=wallet,
        kind=WalletTransaction.KIND_REFUND,
        points=payout.points,
        amount_vnd=payout.amount_vnd,
        note="Hoàn điểm do từ chối quy đổi",
        payout=payout,
    )
