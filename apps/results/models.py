from django.db import models


class Draw(models.Model):
    SIZE_SMALL = "small"
    SIZE_BIG = "big"
    SIZE_CHOICES = [
        (SIZE_SMALL, "Nhỏ"),
        (SIZE_BIG, "Lớn"),
    ]
    PARITY_EVEN = "even"
    PARITY_ODD = "odd"
    PARITY_DRAW = "draw"
    PARITY_CHOICES = [
        (PARITY_EVEN, "Chẵn"),
        (PARITY_ODD, "Lẻ"),
        (PARITY_DRAW, "Hòa"),
    ]

    period_code = models.CharField("Mã kỳ", max_length=20, unique=True, db_index=True)
    draw_date = models.DateField("Ngày quay", db_index=True)
    sequence = models.PositiveIntegerField("Thứ tự trong ngày")
    drawn_at = models.DateTimeField("Thời điểm mở thưởng", db_index=True)
    numbers = models.JSONField("20 số quay", default=list)
    total = models.PositiveIntegerField("Tổng 20 số", default=0)
    size = models.CharField("Lớn/Nhỏ", max_length=8, choices=SIZE_CHOICES, db_index=True)
    even_count = models.PositiveSmallIntegerField("Số lượng số chẵn", default=0)
    odd_count = models.PositiveSmallIntegerField("Số lượng số lẻ", default=0)
    parity = models.CharField("Chẵn/Lẻ", max_length=8, choices=PARITY_CHOICES, db_index=True)
    is_simulated = models.BooleanField(
        "Dữ liệu mô phỏng",
        default=True,
        help_text="Không phải kết quả chính thức.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kỳ quay"
        verbose_name_plural = "Kỳ quay"
        ordering = ["-drawn_at"]
        unique_together = [("draw_date", "sequence")]
        indexes = [
            models.Index(fields=["-drawn_at"]),
            models.Index(fields=["draw_date", "sequence"]),
        ]

    def __str__(self):
        return f"Kỳ {self.period_code}"

    @property
    def numbers_sorted(self):
        return sorted(self.numbers or [])

    @property
    def size_label(self):
        return "Lớn" if self.size == self.SIZE_BIG else "Nhỏ"

    @property
    def parity_label(self):
        return dict(self.PARITY_CHOICES).get(self.parity, self.parity)
