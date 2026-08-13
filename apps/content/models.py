from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.seo.utils import (
    absolute_url,
    count_internal_links,
    first_paragraph,
    images_missing_alt,
    slugify_vi,
)


class ArticleCategory(models.Model):
    name = models.CharField("Tên nhóm", max_length=120)
    slug = models.SlugField("Slug", unique=True)
    description = models.TextField("Mô tả", blank=True)
    sort_order = models.PositiveIntegerField("Thứ tự", default=0)

    class Meta:
        verbose_name = "Nhóm bài viết"
        verbose_name_plural = "Nhóm bài viết"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Article(models.Model):
    category = models.ForeignKey(
        ArticleCategory,
        verbose_name="Nhóm",
        related_name="articles",
        on_delete=models.PROTECT,
    )
    title = models.CharField("Tiêu đề", max_length=200)
    slug = models.SlugField("Slug", unique=True, max_length=220)
    excerpt = models.TextField(
        "Tóm tắt",
        blank=True,
        help_text="1–2 câu tóm tắt.",
    )
    body = models.TextField("Nội dung HTML")
    cover = models.ImageField("Ảnh bìa", upload_to="articles/", blank=True)
    cover_alt = models.CharField("Alt ảnh bìa", max_length=160, blank=True)
    focus_keyword = models.CharField("Từ khóa chính", max_length=80, blank=True)
    seo_title = models.CharField(
        "SEO title",
        max_length=70,
        blank=True,
        help_text="Khuyến nghị ≤ 60 ký tự.",
    )
    seo_description = models.CharField(
        "Meta description",
        max_length=160,
        blank=True,
        help_text="Khuyến nghị ≤ 155 ký tự.",
    )
    canonical_url = models.CharField(
        "Canonical (tùy chọn)",
        max_length=300,
        blank=True,
        help_text="Để trống nếu dùng URL bài.",
    )
    og_image = models.ImageField("Ảnh Open Graph", upload_to="articles/og/", blank=True)
    key_takeaways = models.TextField(
        "Ý chính (mỗi dòng một ý)",
        blank=True,
        help_text="Mỗi dòng một ý.",
    )
    author_name = models.CharField("Tác giả", max_length=120, default="Ban biên tập Keno")
    robots_noindex = models.BooleanField(
        "noindex",
        default=False,
        help_text="Ẩn khỏi sitemap và Google.",
    )
    is_published = models.BooleanField("Xuất bản", default=True)
    published_at = models.DateTimeField("Ngày đăng", default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bài viết SEO"
        verbose_name_plural = "Bài viết SEO"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("content:article_detail", kwargs={"slug": self.slug})

    @property
    def meta_title(self):
        return self.seo_title or self.title

    @property
    def meta_description(self):
        return self.seo_description or (self.excerpt[:160] if self.excerpt else "")

    @property
    def og_image_url(self):
        img = self.og_image or self.cover
        if not img:
            return ""
        return absolute_url(img.url)

    def takeaway_list(self) -> list[str]:
        return [ln.strip(" -•") for ln in (self.key_takeaways or "").splitlines() if ln.strip()]

    def seo_checklist(self) -> list[dict]:
        kw = (self.focus_keyword or "").strip().lower()
        title = (self.seo_title or self.title or "").lower()
        slug = (self.slug or "").lower()
        first = first_paragraph(self.body or "").lower()
        links = count_internal_links(self.body or "")
        missing_alt = images_missing_alt(self.body or "")
        cover_ok = (not self.cover) or bool(self.cover_alt)
        return [
            {"key": "h1", "label": "Có tiêu đề (H1)", "ok": bool(self.title)},
            {
                "key": "kw_title",
                "label": "Từ khóa trong title",
                "ok": bool(kw) and kw in title,
            },
            {
                "key": "kw_slug",
                "label": "Từ khóa trong slug",
                "ok": bool(kw) and (slugify_vi(kw) in slug or kw.replace(" ", "-") in slug),
            },
            {
                "key": "kw_intro",
                "label": "Từ khóa ở đoạn đầu",
                "ok": bool(kw) and kw in first,
            },
            {"key": "links", "label": "Có liên kết nội bộ", "ok": links >= 1, "detail": str(links)},
            {"key": "alts", "label": "Ảnh trong bài có alt", "ok": missing_alt == 0, "detail": str(missing_alt)},
            {"key": "cover", "label": "Alt ảnh bìa", "ok": cover_ok},
            {
                "key": "title_len",
                "label": "SEO title ≤ 60",
                "ok": len(self.seo_title or self.title or "") <= 60,
            },
            {
                "key": "desc_len",
                "label": "Meta description ≤ 160",
                "ok": 40 <= len(self.meta_description or "") <= 160,
            },
        ]


class ArticleFAQ(models.Model):
    article = models.ForeignKey(
        Article, verbose_name="Bài viết", related_name="faqs", on_delete=models.CASCADE
    )
    question = models.CharField("Câu hỏi", max_length=300)
    answer = models.TextField("Câu trả lời")
    sort_order = models.PositiveIntegerField("Thứ tự", default=0)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.question


class StaticPage(models.Model):
    title = models.CharField("Tiêu đề", max_length=200)
    slug = models.SlugField("Slug", unique=True)
    body = models.TextField("Nội dung HTML")
    excerpt = models.TextField("Tóm tắt", blank=True)
    seo_title = models.CharField("SEO title", max_length=70, blank=True)
    seo_description = models.CharField("Meta description", max_length=160, blank=True)
    canonical_url = models.CharField("Canonical (tùy chọn)", max_length=300, blank=True)
    og_image = models.ImageField("Ảnh OG", upload_to="pages/og/", blank=True)
    robots_noindex = models.BooleanField("noindex", default=False)
    is_published = models.BooleanField("Xuất bản", default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Trang tĩnh"
        verbose_name_plural = "Trang tĩnh"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("content:static_page", kwargs={"slug": self.slug})

    @property
    def meta_title(self):
        return self.seo_title or self.title

    @property
    def meta_description(self):
        return self.seo_description or (self.excerpt[:160] if self.excerpt else self.title)
