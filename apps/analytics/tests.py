from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.analytics.models import AnalyticsEvent, CommunityKpiSnapshot, GA4Snapshot, TechnicalKpiSnapshot
from apps.analytics.reports import build_kpi_report, parse_date_range

User = get_user_model()

FUNNEL_STAGES = [
    "Nhận biết",
    "Tiếp cận",
    "Kích hoạt",
    "Gắn kết",
    "Giữ chân",
    "Ý định offline",
    "O2O",
]


class KpiReportTests(TestCase):
    def setUp(self):
        GA4Snapshot.objects.create(
            date="2026-08-01",
            active_users=100,
            new_users=40,
            returning_users=60,
            organic_sessions=55,
            referral_sessions=10,
            sessions=120,
            d7_retention=20,
            d30_retention=9,
        )
        AnalyticsEvent.objects.create(event_name=AnalyticsEvent.RESULT_VIEW, session_key="a")
        CommunityKpiSnapshot.objects.create(
            date=timezone.localdate(),
            new_members=12,
            authentic_account_rate=93,
            returning_active_pct=28,
        )
        TechnicalKpiSnapshot.objects.create(
            date=timezone.localdate(),
            mobile_perf_score=92,
            lcp_ms=1800,
            inp_ms=140,
            cls=0.05,
            realtime_latency_ms=900,
            cwv_pass=True,
        )

    def test_report_keys_match_pdf(self):
        data = build_kpi_report()
        self.assertIn("north_star", data)
        self.assertIn("funnel", data)
        self.assertEqual([s["stage"] for s in data["funnel"]], FUNNEL_STAGES)
        self.assertIn("website_kpis", data)
        self.assertIn("community_kpis", data)
        self.assertIn("o2o", data)
        self.assertIn("technical", data)
        self.assertIn("funnel_chart", data)
        self.assertEqual(len(data["funnel_chart"]), 4)

    def test_website_and_community_kpi_fields(self):
        data = build_kpi_report()
        wk = data["website_kpis"]
        for key in (
            "organic_traffic",
            "organic_growth",
            "keyword_top10",
            "result_check_users",
            "returning_pct",
            "d7",
            "d30",
            "find_pos_ctr",
            "loc_perm_rate",
            "directions_ctr",
        ):
            self.assertIn(key, wk)
        ck = data["community_kpis"]
        for key in (
            "new_members",
            "authentic_rate",
            "approved_per_day",
            "avg_comments",
            "spam_removal_rate",
            "scam_removed",
            "moderation_sla_hours",
            "minigame_participants",
        ):
            self.assertIn(key, ck)
        self.assertTrue(data["technical"]["cwv_pass"])

    def test_date_range_presets(self):
        rf = RequestFactory()
        start, end, preset = parse_date_range(rf.get("/cms/bao-cao/pheu/?range=7"))
        self.assertEqual(preset, "7")
        self.assertEqual((end - start).days, 6)
        start, end, preset = parse_date_range(
            rf.get("/cms/bao-cao/pheu/?start=2026-07-01&end=2026-07-15")
        )
        self.assertEqual(preset, "custom")
        self.assertEqual(str(start), "2026-07-01")


class ReportPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "a@x.local", "pass")
        self.client.force_login(self.user)

    def test_report_pages_render(self):
        names = [
            "admin:index",
            "admin:report_funnel",
            "admin:report_website",
            "admin:report_seo",
            "admin:report_community",
            "admin:report_o2o",
            "admin:analytics_dashboard",
        ]
        for name in names:
            url = reverse(name)
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, name)

    def test_funnel_page_has_north_star(self):
        resp = self.client.get(reverse("admin:report_funnel") + "?range=30")
        self.assertContains(resp, "MAKU")
        self.assertContains(resp, "Nhận biết")
        self.assertContains(resp, "Ý định offline")
