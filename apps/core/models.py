from django.db import models


class SiteSettings(models.Model):
    """Singleton CMS settings for the public site."""

    site_name = models.CharField("Tên website", max_length=120, default="Keno")
    tagline = models.CharField(
        "Khẩu hiệu",
        max_length=200,
        default="Tra cứu kết quả · Cộng đồng · Điểm bán gần bạn",
    )
    facebook_group_url = models.URLField(
        "Link nhóm Facebook",
        blank=True,
        default="https://www.facebook.com/groups/",
    )
    facebook_page_url = models.URLField(
        "Link Facebook Page",
        blank=True,
        default="",
        help_text="Nhúng Page Plugin.",
    )
    facebook_app_id = models.CharField(
        "Facebook App ID",
        max_length=64,
        blank=True,
        default="",
        help_text="Cho plugin bình luận.",
    )
    facebook_comments_url = models.URLField(
        "URL bình luận Facebook",
        blank=True,
        default="",
        help_text="URL trang bình luận.",
    )
    zalo_group_url = models.URLField(
        "Link nhóm Zalo",
        blank=True,
        default="",
        help_text="Nhóm Zalo điểm bán.",
    )
    facebook_group_name = models.CharField(
        "Tên nhóm cộng đồng",
        max_length=160,
        default="Cộng đồng người chơi Keno",
    )
    support_note = models.TextField(
        "Ghi chú trách nhiệm",
        default="Keno chỉ mua tại điểm bán chính thức.",
    )
    ga4_measurement_id = models.CharField("GA4 Measurement ID", max_length=32, blank=True)
    gtm_container_id = models.CharField("GTM Container ID", max_length=32, blank=True)
    community_cta_label = models.CharField(
        "Nhãn CTA cộng đồng",
        max_length=80,
        default="Tham gia cộng đồng",
    )
    pos_cta_label = models.CharField(
        "Nhãn CTA điểm bán",
        max_length=80,
        default="Tìm điểm bán gần bạn",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cài đặt website"
        verbose_name_plural = "Cài đặt website"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Banner(models.Model):
    PLACEMENT_HOME = "home"
    PLACEMENT_COMMUNITY = "community"
    PLACEMENT_POS = "pos"
    PLACEMENT_CHOICES = [
        (PLACEMENT_HOME, "Trang chủ"),
        (PLACEMENT_COMMUNITY, "Cộng đồng"),
        (PLACEMENT_POS, "Điểm bán"),
    ]

    title = models.CharField("Tiêu đề", max_length=160)
    subtitle = models.CharField("Phụ đề", max_length=240, blank=True)
    image = models.ImageField("Hình banner", upload_to="banners/", blank=True)
    link_url = models.CharField("Đường dẫn", max_length=300, blank=True)
    placement = models.CharField(
        "Vị trí", max_length=32, choices=PLACEMENT_CHOICES, default=PLACEMENT_HOME
    )
    is_active = models.BooleanField("Đang hiện", default=True)
    sort_order = models.PositiveIntegerField("Thứ tự", default=0)
    starts_at = models.DateTimeField("Bắt đầu", null=True, blank=True)
    ends_at = models.DateTimeField("Kết thúc", null=True, blank=True)

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banner"
        ordering = ["sort_order", "-id"]

    def __str__(self):
        return self.title
