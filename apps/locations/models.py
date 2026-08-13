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

    class Meta:
        verbose_name = "Điểm bán Keno"
        verbose_name_plural = "Điểm bán Keno"
        ordering = ["city", "name"]

    def __str__(self):
        return f"{self.name} — {self.city}"

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
