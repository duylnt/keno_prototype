from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class PosLocation(models.Model):
    name = models.CharField("Tên điểm bán", max_length=160)
    address = models.CharField("Địa chỉ", max_length=255)
    district = models.CharField("Quận/Huyện", max_length=80, blank=True)
    city = models.CharField("Tỉnh/Thành", max_length=80, db_index=True)
    latitude = models.DecimalField("Vĩ độ", max_digits=9, decimal_places=6)
    longitude = models.DecimalField("Kinh độ", max_digits=9, decimal_places=6)
    phone = models.CharField("Điện thoại", max_length=32, blank=True)
    opening_hours = models.CharField("Giờ mở cửa", max_length=120, blank=True, default="06:00 – 22:00")
    is_active = models.BooleanField("Đang hoạt động", default=True)
    notes = models.CharField("Ghi chú", max_length=200, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Chủ điểm bán",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_pos_locations",
    )

    class Meta:
        verbose_name = "Điểm bán Keno"
        verbose_name_plural = "Điểm bán Keno"
        ordering = ["city", "name"]

    def __str__(self):
        return f"{self.name} — {self.city}"

    @property
    def formatted_address(self) -> str:
        parts = []
        for part in (self.address, self.district, self.city):
            text = (part or "").strip()
            if text and text not in parts:
                parts.append(text)
        return ", ".join(parts)

    def get_absolute_url(self):
        return reverse("locations:pos_detail", kwargs={"pk": self.pk})

    @property
    def maps_directions_url(self):
        return (
            "https://www.google.com/maps/dir/?api=1"
            f"&destination={self.latitude},{self.longitude}"
        )


class ExperienceCode(models.Model):
    """O2O coupon / trial code scanned at POS (prototype)."""

    code = models.CharField("Mã", max_length=16, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField("Hết hạn")
    redeemed_at = models.DateTimeField("Đã quét tại POS", null=True, blank=True)
    pos = models.ForeignKey(
        PosLocation,
        verbose_name="Điểm bán",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="experience_codes",
    )
    pos_name = models.CharField("Điểm bán quét mã", max_length=160, blank=True)
    session_key = models.CharField("Phiên web", max_length=64, blank=True)

    class Meta:
        verbose_name = "Mã trải nghiệm O2O"
        verbose_name_plural = "Mã trải nghiệm O2O"
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    @property
    def is_redeemed(self):
        return self.redeemed_at is not None

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def masked_code(self):
        return mask_code(self.code)


def mask_code(code: str) -> str:
    raw = (code or "").strip()
    if not raw:
        return "••••"
    if len(raw) <= 4:
        return f"{raw[0]}••{raw[-1]}"
    return f"{raw[:2]}•••{raw[-2:]}"


POS_OWNER_GROUP = "pos_owner"


class CommissionLedger(models.Model):
    STATUS_PENDING = "pending"
    STATUS_AVAILABLE = "available"
    STATUS_PAID = "paid"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Chờ ghi nhận"),
        (STATUS_AVAILABLE, "Khả dụng"),
        (STATUS_PAID, "Đã quyết toán (mô phỏng)"),
    ]

    experience_code = models.OneToOneField(
        ExperienceCode,
        verbose_name="Mã O2O",
        on_delete=models.CASCADE,
        related_name="commission",
    )
    pos = models.ForeignKey(
        PosLocation,
        verbose_name="Điểm bán",
        on_delete=models.CASCADE,
        related_name="commissions",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Chủ điểm bán",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pos_commissions",
    )
    amount_vnd = models.PositiveIntegerField("Hoa hồng (VND)", default=0)
    points = models.PositiveIntegerField("Điểm thưởng", default=0)
    status = models.CharField(
        "Trạng thái",
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_AVAILABLE,
        db_index=True,
    )
    created_at = models.DateTimeField("Ghi nhận lúc", default=timezone.now)

    class Meta:
        verbose_name = "Hoa hồng O2O"
        verbose_name_plural = "Hoa hồng O2O"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pos} · {self.amount_vnd}₫"


class OwnerWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="Chủ điểm bán",
        on_delete=models.CASCADE,
        related_name="owner_wallet",
    )
    points_balance = models.PositiveIntegerField("Điểm hiện có", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ví chủ điểm bán"
        verbose_name_plural = "Ví chủ điểm bán"

    def __str__(self):
        return f"{self.user} · {self.points_balance} điểm"

    def vnd_equivalent(self, vnd_per_point: int) -> int:
        rate = int(vnd_per_point or 0)
        return int(self.points_balance) * max(rate, 0)


class WalletTransaction(models.Model):
    KIND_EARN = "earn"
    KIND_PAYOUT = "payout"
    KIND_REFUND = "refund"
    KIND_CHOICES = [
        (KIND_EARN, "Hoa hồng O2O"),
        (KIND_PAYOUT, "Yêu cầu quy đổi"),
        (KIND_REFUND, "Hoàn điểm"),
    ]

    wallet = models.ForeignKey(
        OwnerWallet,
        verbose_name="Ví",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    kind = models.CharField("Loại", max_length=16, choices=KIND_CHOICES, default=KIND_EARN)
    points = models.IntegerField("Điểm (+/−)", default=0)
    amount_vnd = models.IntegerField("VND tương đương", default=0)
    note = models.CharField("Ghi chú", max_length=200, blank=True)
    ledger = models.ForeignKey(
        CommissionLedger,
        verbose_name="Hoa hồng",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wallet_entries",
    )
    payout = models.ForeignKey(
        "PayoutRequest",
        verbose_name="Yêu cầu quy đổi",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wallet_entries",
    )
    created_at = models.DateTimeField("Thời điểm", default=timezone.now)

    class Meta:
        verbose_name = "Biến động ví"
        verbose_name_plural = "Biến động ví"
        ordering = ["-created_at"]

    def __str__(self):
        sign = "+" if self.points >= 0 else ""
        return f"{self.wallet.user} {sign}{self.points}"


class PayoutRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Chờ duyệt"),
        (STATUS_APPROVED, "Đã duyệt"),
        (STATUS_REJECTED, "Từ chối"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Chủ điểm bán",
        on_delete=models.CASCADE,
        related_name="payout_requests",
    )
    points = models.PositiveIntegerField("Điểm quy đổi")
    amount_vnd = models.PositiveIntegerField("Số tiền (VND)")
    status = models.CharField(
        "Trạng thái",
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField("Gửi lúc", default=timezone.now)
    reviewed_at = models.DateTimeField("Duyệt lúc", null=True, blank=True)
    staff_note = models.CharField("Ghi chú CMS", max_length=200, blank=True)

    class Meta:
        verbose_name = "Yêu cầu quy đổi"
        verbose_name_plural = "Yêu cầu quy đổi"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.owner} · {self.points} điểm · {self.get_status_display()}"
