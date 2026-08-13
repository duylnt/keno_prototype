from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import display

from .models import (
    AnalyticsEvent,
    CommunityKpiSnapshot,
    DailyMetric,
    GA4Snapshot,
    GSCQuery,
    GSCSnapshot,
    TechnicalKpiSnapshot,
)
from .views_admin import (
    CommunityReportView,
    FunnelReportView,
    O2OReportView,
    SeoReportView,
    SyncGoogleView,
    WebsiteReportView,
)


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(ModelAdmin):
    list_display = ("event_label", "session_key", "path", "occurred_at")
    list_filter = ("event_name", ("occurred_at", RangeDateFilter))
    search_fields = ("session_key", "path")
    date_hierarchy = "occurred_at"
    list_per_page = 50

    @display(description=_("Sự kiện"))
    def event_label(self, obj):
        return obj.get_event_name_display()


@admin.register(DailyMetric)
class DailyMetricAdmin(ModelAdmin):
    list_display = ("date", "source", "metric_name", "value")
    list_filter = ("source", "metric_name", ("date", RangeDateFilter))
    search_fields = ("metric_name",)
    list_per_page = 50


@admin.register(GA4Snapshot)
class GA4SnapshotAdmin(ModelAdmin):
    list_display = (
        "date",
        "active_users",
        "new_users",
        "organic_sessions",
        "d7_retention",
        "d30_retention",
        "synced_at",
    )
    list_filter = (("date", RangeDateFilter),)
    list_per_page = 50


@admin.register(GSCSnapshot)
class GSCSnapshotAdmin(ModelAdmin):
    list_display = ("date", "clicks", "impressions", "ctr", "position", "synced_at")
    list_filter = (("date", RangeDateFilter),)
    list_per_page = 50


@admin.register(GSCQuery)
class GSCQueryAdmin(ModelAdmin):
    list_display = ("date", "query", "clicks", "impressions", "ctr", "position")
    list_filter = (("date", RangeDateFilter),)
    search_fields = ("query", "page")
    list_per_page = 50


@admin.register(CommunityKpiSnapshot)
class CommunityKpiSnapshotAdmin(ModelAdmin):
    list_display = ("date", "new_members", "authentic_account_rate", "returning_active_pct")
    list_filter = (("date", RangeDateFilter),)
    list_per_page = 50


@admin.register(TechnicalKpiSnapshot)
class TechnicalKpiSnapshotAdmin(ModelAdmin):
    list_display = (
        "date",
        "mobile_perf_score",
        "lcp_ms",
        "inp_ms",
        "cls",
        "realtime_latency_ms",
        "cwv_pass",
    )
    list_filter = ("cwv_pass", ("date", RangeDateFilter))
    list_per_page = 50


def _register_custom_admin_urls():
    original = admin.site.get_urls

    def get_urls():
        extra = [
            path(
                "bao-cao/pheu/",
                admin.site.admin_view(FunnelReportView.as_view()),
                name="report_funnel",
            ),
            path(
                "bao-cao/website/",
                admin.site.admin_view(WebsiteReportView.as_view()),
                name="report_website",
            ),
            path(
                "bao-cao/seo/",
                admin.site.admin_view(SeoReportView.as_view()),
                name="report_seo",
            ),
            path(
                "bao-cao/cong-dong/",
                admin.site.admin_view(CommunityReportView.as_view()),
                name="report_community",
            ),
            path(
                "bao-cao/o2o/",
                admin.site.admin_view(O2OReportView.as_view()),
                name="report_o2o",
            ),
            path(
                "bao-cao-kpi/",
                admin.site.admin_view(FunnelReportView.as_view()),
                name="analytics_dashboard",
            ),
            path(
                "dong-bo-google/",
                admin.site.admin_view(SyncGoogleView.as_view()),
                name="analytics_sync_google",
            ),
        ]
        return extra + original()

    admin.site.get_urls = get_urls


_register_custom_admin_urls()
