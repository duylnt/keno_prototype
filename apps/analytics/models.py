from django.db import models
from django.utils import timezone


class AnalyticsEvent(models.Model):
    RESULT_VIEW = "result_view"
    STATS_VIEW = "stats_view"
    TICKET_CHECK = "ticket_check"
    SIMULATOR_PLAY = "simulator_play"
    FIND_POS_CLICK = "find_pos_click"
    POS_SEARCH = "pos_search"
    POS_DETAIL = "pos_detail"
    GET_DIRECTIONS = "get_directions"
    LOCATION_PERMISSION = "location_permission"
    COMMUNITY_CTA = "community_cta"
    COMMUNITY_JOIN_INTENT = "community_join_intent"
    VOUCHER_ISSUE = "voucher_issue"

    EVENT_CHOICES = [
        (RESULT_VIEW, "Xem kết quả"),
        (STATS_VIEW, "Xem thống kê"),
        (TICKET_CHECK, "Dò vé"),
        (SIMULATOR_PLAY, "Chơi thử"),
        (FIND_POS_CLICK, "Nhấp Tìm điểm bán"),
        (POS_SEARCH, "Tìm kiếm điểm bán"),
        (POS_DETAIL, "Xem chi tiết điểm bán"),
        (GET_DIRECTIONS, "Nhấp Chỉ đường"),
        (LOCATION_PERMISSION, "Cấp quyền vị trí"),
        (COMMUNITY_CTA, "CTA cộng đồng"),
        (COMMUNITY_JOIN_INTENT, "Ý định tham gia nhóm"),
        (VOUCHER_ISSUE, "Nhận mã O2O"),
    ]

    event_name = models.CharField("Sự kiện", max_length=48, choices=EVENT_CHOICES, db_index=True)
    session_key = models.CharField("Phiên", max_length=64, db_index=True, blank=True)
    path = models.CharField("Đường dẫn", max_length=255, blank=True)
    metadata = models.JSONField("Metadata", default=dict, blank=True)
    occurred_at = models.DateTimeField("Thời điểm", default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Sự kiện nội bộ"
        verbose_name_plural = "Sự kiện nội bộ"
        ordering = ["-occurred_at"]
        indexes = [models.Index(fields=["event_name", "occurred_at"])]

    def __str__(self):
        return f"{self.get_event_name_display()} @ {self.occurred_at:%Y-%m-%d %H:%M}"


class DailyMetric(models.Model):
    SOURCE_INTERNAL = "internal"
    SOURCE_GA4 = "ga4"
    SOURCE_GSC = "gsc"
    SOURCE_CHOICES = [
        (SOURCE_INTERNAL, "Nội bộ"),
        (SOURCE_GA4, "Google Analytics 4"),
        (SOURCE_GSC, "Search Console"),
    ]

    date = models.DateField("Ngày", db_index=True)
    source = models.CharField("Nguồn", max_length=16, choices=SOURCE_CHOICES)
    metric_name = models.CharField("Chỉ số", max_length=64, db_index=True)
    value = models.FloatField("Giá trị", default=0)
    extra = models.JSONField("Chi tiết", default=dict, blank=True)

    class Meta:
        verbose_name = "KPI hàng ngày"
        verbose_name_plural = "KPI hàng ngày"
        unique_together = [("date", "source", "metric_name")]
        ordering = ["-date", "metric_name"]

    def __str__(self):
        return f"{self.date} {self.metric_name}={self.value}"


class GA4Snapshot(models.Model):
    date = models.DateField("Ngày", unique=True)
    active_users = models.PositiveIntegerField("Người dùng hoạt động", default=0)
    new_users = models.PositiveIntegerField("Người dùng mới", default=0)
    returning_users = models.PositiveIntegerField("Người dùng quay lại", default=0)
    sessions = models.PositiveIntegerField("Phiên", default=0)
    organic_sessions = models.PositiveIntegerField("Phiên organic", default=0)
    referral_sessions = models.PositiveIntegerField("Phiên referral", default=0)
    engaged_sessions = models.PositiveIntegerField("Phiên tương tác", default=0)
    bounce_rate = models.FloatField("Tỷ lệ thoát (%)", default=0)
    avg_session_duration = models.FloatField("Thời lượng phiên (s)", default=0)
    pages_per_session = models.FloatField("Số trang / phiên", default=0)
    d7_retention = models.FloatField("Giữ chân D7 (%)", default=0)
    d30_retention = models.FloatField("Giữ chân D30 (%)", default=0)
    synced_at = models.DateTimeField("Đồng bộ lúc", auto_now=True)
    raw_payload = models.JSONField("Payload thô", default=dict, blank=True)

    class Meta:
        verbose_name = "GA4 snapshot"
        verbose_name_plural = "GA4 snapshots"
        ordering = ["-date"]

    def __str__(self):
        return f"GA4 {self.date}"


class GSCSnapshot(models.Model):
    date = models.DateField("Ngày", unique=True)
    clicks = models.PositiveIntegerField("Clicks", default=0)
    impressions = models.PositiveIntegerField("Impressions", default=0)
    ctr = models.FloatField("CTR (%)", default=0)
    position = models.FloatField("Vị trí TB", default=0)
    synced_at = models.DateTimeField("Đồng bộ lúc", auto_now=True)

    class Meta:
        verbose_name = "Search Console snapshot"
        verbose_name_plural = "Search Console snapshots"
        ordering = ["-date"]

    def __str__(self):
        return f"GSC {self.date}"


class GSCQuery(models.Model):
    date = models.DateField("Ngày", db_index=True)
    query = models.CharField("Từ khóa", max_length=255, db_index=True)
    clicks = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    ctr = models.FloatField("CTR (%)", default=0)
    position = models.FloatField("Vị trí", default=0)
    page = models.CharField("URL", max_length=400, blank=True)

    class Meta:
        verbose_name = "Từ khóa Search Console"
        verbose_name_plural = "Từ khóa Search Console"
        unique_together = [("date", "query")]
        ordering = ["-date", "-clicks"]

    def __str__(self):
        return f"{self.query} ({self.date})"


class CommunityKpiSnapshot(models.Model):

    date = models.DateField("Ngày", unique=True)
    new_members = models.PositiveIntegerField("Thành viên mới", default=0)
    authentic_account_rate = models.FloatField("Tỷ lệ tài khoản xác thực (%)", default=0)
    returning_active_pct = models.FloatField("Thành viên hoạt động quay lại (%)", default=0)
    notes = models.CharField("Ghi chú", max_length=240, blank=True)

    class Meta:
        verbose_name = "KPI cộng đồng"
        verbose_name_plural = "KPI cộng đồng"
        ordering = ["-date"]

    def __str__(self):
        return f"Cộng đồng {self.date}"


class TechnicalKpiSnapshot(models.Model):

    date = models.DateField("Ngày", unique=True)
    mobile_perf_score = models.FloatField("Điểm hiệu suất mobile", default=0)
    lcp_ms = models.FloatField("LCP (ms)", default=0)
    inp_ms = models.FloatField("INP (ms)", default=0)
    cls = models.FloatField("CLS", default=0)
    realtime_latency_ms = models.FloatField("Độ trễ realtime (ms)", default=0)
    cwv_pass = models.BooleanField("Core Web Vitals đạt chuẩn", default=False)

    class Meta:
        verbose_name = "KPI kỹ thuật"
        verbose_name_plural = "KPI kỹ thuật"
        ordering = ["-date"]

    def __str__(self):
        return f"Kỹ thuật {self.date}"
