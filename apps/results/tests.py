from django.test import TestCase
from django.urls import reverse

from apps.results.models import Draw
from apps.results.services import (
    attributes_for,
    consecutive_streaks,
    ensure_draws_up_to_now,
    period_code,
    pos_tv_payload,
    tv_ball_stats,
)


class DrawLogicTests(TestCase):
    def test_attributes_big_even(self):
        numbers = list(range(61, 81))
        attrs = attributes_for(numbers)
        self.assertEqual(len(numbers), 20)
        self.assertEqual(attrs["size"], Draw.SIZE_BIG)
        self.assertGreater(attrs["total"], 810)

    def test_period_code_format(self):
        from datetime import date

        self.assertEqual(period_code(date(2026, 8, 13), 3), "20260813-003")

    def test_ensure_draws_creates_history(self):
        created = ensure_draws_up_to_now(lookback_days=0)
        self.assertGreaterEqual(created, 0)
        self.assertTrue(Draw.objects.exists() or created == 0)


class PublicViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ensure_draws_up_to_now(lookback_days=0)

    def test_home_ok(self):
        r = self.client.get(reverse("core:home"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "desk-header")
        self.assertContains(r, "tabbar")
        self.assertContains(r, "live-tab--desk")
        self.assertContains(r, "live-tab--tabbar")
        self.assertContains(r, reverse("core:live_results"))
        self.assertContains(r, "Trực tiếp quay số")
        self.assertContains(r, 'aria-label="Trực tiếp quay số"')
        self.assertContains(r, 'title="Trực tiếp quay số"')
        self.assertContains(r, "live-badge-led")
        self.assertNotContains(r, "live-badge-word")
        self.assertNotContains(r, "nav-live")
        self.assertContains(r, "homeSizeChart")
        self.assertIn("stats", r.context)
        self.assertIn("today_count", r.context["stats"])

    def test_live_ok(self):
        r = self.client.get(reverse("results:live"))
        self.assertEqual(r.status_code, 200)

    def test_stats_ok(self):
        r = self.client.get(reverse("results:stats"))
        self.assertEqual(r.status_code, 200)

    def test_finder_ok(self):
        r = self.client.get(reverse("locations:finder"))
        self.assertEqual(r.status_code, 200)

    def test_community_ok(self):
        r = self.client.get(reverse("community:hub"))
        self.assertEqual(r.status_code, 200)

    def test_live_api_json(self):
        r = self.client.get(reverse("results:live_api"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("countdown", r.json())

    def test_sitemap(self):
        r = self.client.get("/sitemap.xml")
        self.assertEqual(r.status_code, 200)

    def test_track_event(self):
        r = self.client.post(
            reverse("analytics:collect"),
            data='{"event":"result_view"}',
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])

    def test_pos_display_tv_loop(self):
        r = self.client.get(reverse("core:pos_display"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "desk-header")
        self.assertContains(r, "live-tab--desk is-active")
        self.assertContains(r, "Trực tiếp kết quả")
        self.assertContains(r, "CHÀO MỪNG BẠN ĐẾN VỚI")
        self.assertContains(r, "CHUẨN BỊ DỪNG BÁN VÉ")
        self.assertContains(r, "CẦM VÉ TRÊN TAY")
        self.assertContains(r, "SỐ VỀ NHIỀU")
        self.assertContains(r, "SỐ KHÔNG VỀ LIÊN TỤC")
        self.assertContains(r, "pos-tv.css")
        self.assertContains(r, "pos-tv.js")
        self.assertContains(r, "live-stage-frame")
        self.assertContains(r, "Thảo luận cộng đồng")
        self.assertNotContains(r, "Toàn màn hình")
        self.assertNotContains(r, "pos-fs-btn")
        self.assertNotContains(r, "convert-stack")
        self.assertNotContains(r, "fitStage")
        self.assertIn("pos", r.context)

    def test_live_results_aliases(self):
        for name in ("core:pos_display", "core:pos_tv", "core:live_results", "core:live_results_short"):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)
            self.assertContains(r, "Trực tiếp kết quả")

    def test_pos_tv_alias_and_api(self):
        r = self.client.get(reverse("core:pos_tv"))
        self.assertEqual(r.status_code, 200)
        api = self.client.get(reverse("core:pos_tv_api"))
        self.assertEqual(api.status_code, 200)
        body = api.json()
        self.assertIn("countdown", body)
        self.assertIn("hot5", body)
        self.assertIn("chart_size", body)
        self.assertIn("miss_streaks", body)

    def test_finder_gps_flag(self):
        r = self.client.get(reverse("locations:finder") + "?gps=1")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-auto-gps="1"')

    def test_home_header_convert_ctas(self):
        r = self.client.get(reverse("core:home"))
        self.assertContains(r, "Mua vé")
        self.assertContains(r, "Tham gia cộng đồng")
        self.assertNotContains(r, "Màn hình quầy")


class PosTvLogicTests(TestCase):
    def test_tv_ball_stats_all_small(self):
        stats = tv_ball_stats(list(range(1, 21)))
        self.assertEqual(stats["small"], 20)
        self.assertEqual(stats["size_label"], "NHỎ")
        self.assertEqual(stats["even"], 10)
        self.assertEqual(stats["parity_label"], "HOÀ")

    def test_tv_ball_stats_all_big(self):
        stats = tv_ball_stats(list(range(61, 81)))
        self.assertEqual(stats["big"], 20)
        self.assertEqual(stats["size_label"], "LỚN")

    def test_consecutive_streaks_and_payload(self):
        ensure_draws_up_to_now(lookback_days=1)
        payload = pos_tv_payload()
        self.assertIn("latest", payload)
        self.assertEqual(len(payload["hot5"]), 10)
        hits, misses = consecutive_streaks(list(Draw.objects.all()[:20]))
        self.assertIsInstance(hits, list)
        self.assertIsInstance(misses, list)
