from django.db import models
from django.utils import timezone


class SeoRedirect(models.Model):
    from_path = models.CharField(
        "Đường dẫn cũ",
        max_length=300,
        unique=True,
        help_text="Ví dụ: /keno/ hoặc /bai-cu/",
    )
    to_path = models.CharField(
        "Đường dẫn mới",
        max_length=300,
        help_text="Ví dụ: /huong-dan/ hoặc URL đầy đủ",
    )
    is_permanent = models.BooleanField("301 (vĩnh viễn)", default=True)
    is_active = models.BooleanField("Đang dùng", default=True)
    note = models.CharField("Ghi chú", max_length=200, blank=True)
    hit_count = models.PositiveIntegerField("Lượt chuyển", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Redirect 301"
        verbose_name_plural = "Redirect 301"
        ordering = ["from_path"]

    def __str__(self):
        return f"{self.from_path} → {self.to_path}"


class ResearchUrl(models.Model):
    STATUS_OK = "ok"
    STATUS_BLOCKED = "blocked"
    STATUS_ERROR = "error"
    STATUS_SAMPLE = "sample"
    STATUS_CHOICES = [
        (STATUS_OK, "Đã phân tích"),
        (STATUS_BLOCKED, "robots.txt chặn"),
        (STATUS_ERROR, "Lỗi / timeout"),
        (STATUS_SAMPLE, "Mẫu minh họa"),
    ]
    PRODUCT_CHOICES = [
        ("keno", "Keno"),
        ("power655", "Power 6/55"),
        ("mega645", "Mega 6/45"),
        ("max3d", "Max 3D"),
        ("lotto535", "Lotto 5/35"),
        ("other", "Khác"),
    ]

    url = models.URLField("URL", max_length=500)
    product_hint = models.CharField(
        "Sản phẩm", max_length=20, choices=PRODUCT_CHOICES, default="keno"
    )
    title = models.CharField("Tiêu đề", max_length=300, blank=True)
    meta_description = models.CharField("Meta description", max_length=400, blank=True)
    canonical = models.CharField("Canonical", max_length=500, blank=True)
    headings = models.JSONField("Heading", default=list, blank=True)
    outline = models.TextField("Dàn ý (heading)", blank=True)
    excerpt = models.TextField(
        "Đoạn trích ngắn",
        blank=True,
        help_text="Tối đa ~400 ký tự.",
    )
    word_count = models.PositiveIntegerField("Số từ (ước tính)", default=0)
    keyword_hints = models.CharField("Gợi ý từ khóa", max_length=400, blank=True)
    schema_types = models.CharField("Schema", max_length=200, blank=True)
    published_hint = models.CharField("Ngày đăng (nếu có)", max_length=80, blank=True)
    http_status = models.PositiveSmallIntegerField("HTTP", null=True, blank=True)
    robots_allowed = models.BooleanField("robots.txt cho phép", default=True)
    status = models.CharField("Trạng thái", max_length=12, choices=STATUS_CHOICES, default=STATUS_OK)
    error_message = models.CharField("Lỗi", max_length=300, blank=True)
    fetched_at = models.DateTimeField("Phân tích lúc", default=timezone.now)

    class Meta:
        verbose_name = "URL thị trường"
        verbose_name_plural = "Nội dung thị trường"
        ordering = ["-fetched_at"]

    def __str__(self):
        return self.title or self.url

    @property
    def keyword_list(self) -> list[str]:
        return [k.strip() for k in (self.keyword_hints or "").split(",") if k.strip()]


class BrokenLink(models.Model):
    source_path = models.CharField("Trang nguồn", max_length=300)
    target_url = models.CharField("Link", max_length=500)
    status_code = models.PositiveSmallIntegerField("Mã HTTP", default=0)
    is_internal = models.BooleanField("Nội bộ", default=True)
    checked_at = models.DateTimeField("Kiểm tra lúc", default=timezone.now)

    class Meta:
        verbose_name = "Link hỏng"
        verbose_name_plural = "Link hỏng"
        ordering = ["-checked_at"]

    def __str__(self):
        return f"{self.source_path} → {self.target_url} ({self.status_code})"


class CoreWebVitalsNote(models.Model):
    """Manual CWV checklist — never fake Lighthouse scores."""

    date = models.DateField("Ngày ghi", default=timezone.localdate)
    lcp_note = models.CharField("LCP (ghi chú tay)", max_length=200, blank=True)
    inp_note = models.CharField("INP (ghi chú tay)", max_length=200, blank=True)
    cls_note = models.CharField("CLS (ghi chú tay)", max_length=200, blank=True)
    notes = models.TextField(
        "Checklist thủ công",
        blank=True,
        default=(
            "- Ảnh bìa có width/height hoặc CSS cố định?\n"
            "- Font: preconnect Google Fonts?\n"
            "- Chart.js / Leaflet chỉ load trên trang cần?"
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ghi chú Core Web Vitals"
        verbose_name_plural = "Ghi chú Core Web Vitals"
        ordering = ["-date"]

    def __str__(self):
        return f"CWV {self.date}"


class SeoStatus(models.Model):
    """Singleton: sitemap / link-check timestamps."""

    sitemap_generated_at = models.DateTimeField(null=True, blank=True)
    linkcheck_at = models.DateTimeField(null=True, blank=True)
    linkcheck_ok = models.PositiveIntegerField(default=0)
    linkcheck_broken = models.PositiveIntegerField(default=0)
    research_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Trạng thái công cụ SEO"
        verbose_name_plural = "Trạng thái công cụ SEO"

    def __str__(self):
        return "SEO status"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
