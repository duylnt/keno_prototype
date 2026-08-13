from django.db import models
from django.utils import timezone


class CommunityGuideline(models.Model):
    title = models.CharField("Tiêu đề", max_length=160)
    body = models.TextField("Nội dung HTML")
    sort_order = models.PositiveIntegerField("Thứ tự", default=0)
    is_active = models.BooleanField("Đang dùng", default=True)

    class Meta:
        verbose_name = "Nội quy cộng đồng"
        verbose_name_plural = "Nội quy cộng đồng"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class JoinQuestion(models.Model):
    question = models.CharField("Câu hỏi lọc thành viên", max_length=300)
    hint = models.CharField("Gợi ý đáp án đúng", max_length=200, blank=True)
    sort_order = models.PositiveIntegerField("Thứ tự", default=0)
    is_active = models.BooleanField("Đang dùng", default=True)

    class Meta:
        verbose_name = "Câu hỏi lọc"
        verbose_name_plural = "Câu hỏi lọc thành viên"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.question


class BannedKeyword(models.Model):
    keyword = models.CharField("Từ khóa", max_length=80, unique=True)
    reason = models.CharField("Lý do", max_length=160, blank=True)
    is_active = models.BooleanField("Đang lọc", default=True)

    class Meta:
        verbose_name = "Từ khóa cấm"
        verbose_name_plural = "Từ khóa cấm"

    def __str__(self):
        return self.keyword


class CommunityPost(models.Model):
    PILLAR_REALTIME = "realtime"
    PILLAR_KNOWLEDGE = "knowledge"
    PILLAR_DATA = "data"
    PILLAR_COMMUNITY = "community"
    PILLAR_ENTERTAINMENT = "entertainment"
    PILLAR_CHOICES = [
        (PILLAR_REALTIME, "Keno Real-time"),
        (PILLAR_KNOWLEDGE, "Keno Knowledge"),
        (PILLAR_DATA, "Keno Data"),
        (PILLAR_COMMUNITY, "Keno Community"),
        (PILLAR_ENTERTAINMENT, "Keno Entertainment"),
    ]
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Chờ duyệt"),
        (STATUS_APPROVED, "Đã duyệt"),
        (STATUS_REJECTED, "Từ chối / spam"),
    ]

    title = models.CharField("Chủ đề", max_length=200)
    body = models.TextField("Nội dung")
    author_name = models.CharField("Người đăng", max_length=80, default="Ban quản trị")
    pillar = models.CharField(
        "Nhóm nội dung", max_length=24, choices=PILLAR_CHOICES, default=PILLAR_COMMUNITY
    )
    status = models.CharField(
        "Trạng thái", max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    is_featured = models.BooleanField("Nổi bật trên widget", default=False)
    comment_count = models.PositiveIntegerField("Số bình luận (ước tính)", default=0)
    rejection_reason = models.CharField("Lý do từ chối", max_length=200, blank=True)
    created_at = models.DateTimeField("Thời điểm", default=timezone.now)
    moderated_at = models.DateTimeField("Duyệt lúc", null=True, blank=True)

    class Meta:
        verbose_name = "Bài thảo luận"
        verbose_name_plural = "Bài thảo luận cộng đồng"
        ordering = ["-is_featured", "-created_at"]

    def __str__(self):
        return self.title


class FacebookPagePost(models.Model):
    """Cached published Page posts from Graph API — never scraped HTML."""

    fb_id = models.CharField("Facebook post ID", max_length=80, unique=True)
    message = models.TextField("Nội dung", blank=True)
    created_time = models.DateTimeField("Đăng lúc", null=True, blank=True)
    permalink = models.URLField("Permalink", max_length=500, blank=True)
    is_published = models.BooleanField("Đang công khai", default=True)
    is_hidden = models.BooleanField("Đã ẩn", default=False)
    synced_at = models.DateTimeField("Đồng bộ lúc", auto_now=True)
    last_api_error = models.CharField("Lỗi API gần nhất", max_length=300, blank=True)

    class Meta:
        verbose_name = "Bài Fanpage (cache)"
        verbose_name_plural = "Bài Fanpage (cache)"
        ordering = ["-created_time", "-id"]

    def __str__(self):
        text = (self.message or "").strip().replace("\n", " ")
        return (text[:72] + "…") if len(text) > 72 else (text or self.fb_id)


class MinigameEvent(models.Model):
    title = models.CharField("Tên hoạt động", max_length=160)
    description = models.TextField("Mô tả")
    scheduled_at = models.DateTimeField("Thời điểm")
    reward_note = models.CharField(
        "Phần thưởng (nếu có)",
        max_length=160,
        blank=True,
        help_text="Không cam kết trúng thưởng.",
    )
    is_published = models.BooleanField("Công khai", default=True)
    participants = models.PositiveIntegerField("Lượt tham gia", default=0)

    class Meta:
        verbose_name = "Minigame / hoạt động"
        verbose_name_plural = "Minigame cộng đồng"
        ordering = ["-scheduled_at"]

    def __str__(self):
        return self.title
