from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.analytics.models import AnalyticsEvent, GA4Snapshot, GSCSnapshot
from apps.analytics.reports import build_kpi_report
from apps.community.models import CommunityPost
from apps.content.models import Article
from apps.locations.models import ExperienceCode, PosLocation
from apps.results.models import Draw
from apps.results.services import latest_draw


def dashboard_callback(request, context):
    report = build_kpi_report(request)
    today = timezone.localdate()
    week = today - timedelta(days=7)
    events = AnalyticsEvent.objects.filter(occurred_at__date__gte=week)
    event_counts = dict(
        events.values_list("event_name").annotate(c=Count("id")).values_list("event_name", "c")
    )
    ga4 = GA4Snapshot.objects.order_by("-date").first()
    gsc = GSCSnapshot.objects.order_by("-date").first()
    latest = latest_draw()

    ns = report["north_star"]
    wk = report["website_kpis"]
    ck = report["community_kpis"]
    o2o = report["o2o"]

    context.update(
        {
            "keno_kpis": [
                {
                    "label": "MAKU",
                    "value": ns["value"],
                    "hint": "Phiên hoạt động",
                },
                {
                    "label": "Người dùng xem kết quả",
                    "value": wk["result_check_users"],
                    "hint": "Kích hoạt",
                },
                {
                    "label": "Phiên organic",
                    "value": wk["organic_traffic"],
                    "hint": (
                        f"Tăng trưởng {wk['organic_growth']}%"
                        if wk["has_organic_growth"]
                        else "Cần đủ dữ liệu kỳ trước để so sánh"
                    ),
                },
                {
                    "label": "Từ khóa Top 10",
                    "value": wk["keyword_top10"],
                    "hint": "Search Console",
                },
                {
                    "label": "Ý định POS",
                    "value": o2o["intent_sessions"],
                    "hint": f"CTR tìm điểm bán {o2o['find_pos_ctr']}%",
                },
                {
                    "label": "Mã O2O đã quét",
                    "value": o2o["redeemed"],
                    "hint": f"{o2o['issued']} mã phát hành",
                },
                {
                    "label": "Giữ chân D7",
                    "value": f"{wk['d7']}%",
                    "hint": f"D30 {wk['d30']}%",
                },
                {
                    "label": "Bài chờ duyệt",
                    "value": ck["pending"],
                    "hint": f"{ck['approved_per_day']} bài duyệt/ngày",
                },
            ],
            "keno_ga4": ga4,
            "keno_gsc": gsc,
            "keno_pending_posts": ck["pending"],
            "keno_pos_count": PosLocation.objects.filter(is_active=True).count(),
            "keno_draw": latest,
            "keno_draw_count": Draw.objects.count(),
            "keno_o2o_week": ExperienceCode.objects.filter(created_at__date__gte=week).count(),
            "keno_articles": Article.objects.filter(is_published=True).count(),
            "keno_event_counts": event_counts,
            "keno_ga4_series": report["ga4_series"],
            "keno_funnel": report["funnel_chart"],
            "keno_shortcuts": [
                {"title": "Phễu tăng trưởng", "url_name": "admin:report_funnel", "icon": "filter_alt"},
                {"title": "KPI Website", "url_name": "admin:report_website", "icon": "language"},
                {"title": "Search Console", "url_name": "admin:report_seo", "icon": "travel_explore"},
                {"title": "KPI Cộng đồng", "url_name": "admin:report_community", "icon": "groups"},
                {"title": "Ý định O2O", "url_name": "admin:report_o2o", "icon": "qr_code_2"},
                {"title": "Bài viết SEO", "url_name": "admin:content_article_changelist", "icon": "edit_note"},
            ],
            "report": report,
        }
    )
    return context
