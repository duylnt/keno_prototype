from django.test import TestCase
from django.urls import reverse

from apps.results.models import Draw
from apps.results.prizes import basic_amount, evaluate_basic, evaluate_parity, evaluate_sim, evaluate_size
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

    def test_simulator_has_howto(self):
        r = self.client.get(reverse("results:simulator"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Cách chơi Keno")
        self.assertContains(r, "Cách chơi cơ bản")
        self.assertContains(r, "Lớn / Nhỏ")
        self.assertContains(r, "Chẵn / Lẻ")
        self.assertContains(r, "210–810")
        self.assertContains(r, "811–1410")
        self.assertContains(r, "không dùng tiền thật")
        self.assertContains(r, reverse("content:how_to_play"))
        self.assertContains(r, 'id="cach-choi"')
        self.assertContains(r, 'id="bang-thuong"')
        self.assertContains(r, "Bảng thưởng mô phỏng")
        self.assertContains(r, "2.000.000.000 ₫")
        self.assertContains(r, "20.000 ₫")
        self.assertContains(r, "56.000 ₫")
        self.assertContains(r, "210.000 ₫")
        self.assertContains(r, 'id="sim-prize"')
        self.assertContains(r, 'id="sim-prize-dialog"')
        self.assertContains(r, 'id="sim-prize-notice"')
        self.assertContains(r, 'id="sim-form"')
        self.assertNotContains(r, 'id="sim-play-boot"')
        self.assertContains(r, "keno.js")
        self.assertContains(r, "Kết quả kỳ quay vừa rồi")
        self.assertContains(r, "Thông báo trúng thưởng")

    def test_simulator_play_returns_prize(self):
        r = self.client.post(
            reverse("results:simulator_play"),
            data='{"numbers":[1,2,3,4,5]}',
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("prize", body)
        basic = body["prize"]["basic"]
        self.assertEqual(basic["pick_count"], 5)
        self.assertIn("amount", basic)
        self.assertIn("headline", basic)
        self.assertIn("size", body["prize"])
        self.assertIn("parity", body["prize"])
        self.assertIn("không chi trả", body["prize"]["note"])
        self.assertIn("popup_title", body["prize"])
        self.assertIn("popup_body", body["prize"])
        self.assertIn("notice_lead", body["prize"])
        self.assertIn("won", body["prize"])
        self.assertIn("total_amount", body["prize"])

    def test_simulator_post_bootstraps_prize_popup(self):
        r = self.client.post(reverse("results:simulator"), {"numbers": "1,2,3,4,5"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="sim-play-boot"')
        self.assertContains(r, "popup_title")
        self.assertContains(r, "Chúc")
        self.assertContains(r, 'id="sim-form"')
        self.assertContains(r, 'id="sim-prize-dialog"')
        self.assertNotContains(r, 'id="sim-result" hidden')
        boot = r.context["sim_play"]
        self.assertEqual(boot["picked"], [1, 2, 3, 4, 5])
        self.assertEqual(len(boot["drawn"]), 20)
        self.assertIn(boot["prize"]["popup_title"], ("Chúc mừng bạn đã thắng", "Chúc may mắn lần sau"))
        self.assertIn("won", boot["prize"])
        self.assertIn("notice_lead", boot["prize"])

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
        self.assertContains(r, "CHUẨN BỊ")
        self.assertContains(r, "DỪNG BÁN VÉ")
        self.assertContains(r, "CẦM VÉ TRÊN TAY")
        self.assertContains(r, "SỐ VỀ NHIỀU")
        self.assertContains(r, "SỐ KHÔNG VỀ LIÊN TỤC")
        self.assertContains(r, "pos-tv.css")
        self.assertContains(r, "pos-tv.js")
        self.assertContains(r, "live-stage-frame")
        self.assertContains(r, "live-community")
        self.assertContains(r, "Thảo luận cộng đồng")
        self.assertNotContains(r, "live-sidebar")
        self.assertNotContains(r, "live-cd")
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


class PrizeTableTests(TestCase):
    def test_basic_payouts_from_article_matrix(self):
        self.assertEqual(basic_amount(1, 1), 20_000)
        self.assertEqual(basic_amount(2, 2), 90_000)
        self.assertEqual(basic_amount(5, 4), 150_000)
        self.assertEqual(basic_amount(5, 2), 0)
        self.assertEqual(basic_amount(8, 0), 10_000)
        self.assertEqual(basic_amount(8, 4), 10_000)
        self.assertEqual(basic_amount(10, 0), 10_000)
        self.assertEqual(basic_amount(10, 10), 2_000_000_000)
        self.assertEqual(basic_amount(10, 8), 7_400_000)

    def test_basic_zero_match_on_low_tier_is_miss(self):
        result = evaluate_basic([1, 2, 3], list(range(20, 40)))
        self.assertFalse(result["won"])
        self.assertEqual(result["amount"], 0)
        self.assertEqual(result["headline"], "Không trúng")

    def test_basic_no_picks(self):
        result = evaluate_basic([], list(range(1, 21)))
        self.assertEqual(result["headline"], "Chưa chọn số")
        self.assertFalse(result["won"])

    def test_size_prize_needs_thirteen(self):
        big13 = list(range(41, 54)) + list(range(1, 8))
        self.assertEqual(len(big13), 20)
        hit = evaluate_size(big13)
        self.assertTrue(hit["won"])
        self.assertEqual(hit["amount"], 56_000)
        self.assertIn("Lớn", hit["name"])
        miss = evaluate_size(list(range(1, 11)) + list(range(41, 51)))
        self.assertFalse(miss["won"])
        self.assertEqual(miss["amount"], 0)

    def test_parity_prize_tiers(self):
        even15 = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 1, 3, 5, 7, 9]
        top = evaluate_parity(even15)
        self.assertTrue(top["won"])
        self.assertEqual(top["amount"], 210_000)
        even13 = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 1, 3, 5, 7, 9, 11, 13]
        mid = evaluate_parity(even13)
        self.assertEqual(mid["amount"], 40_000)
        split = evaluate_parity(list(range(1, 21)))
        self.assertFalse(split["won"])
        self.assertEqual(split["amount"], 0)

    def test_evaluate_sim_payload(self):
        payload = evaluate_sim([1], list(range(1, 21)))
        self.assertTrue(payload["basic"]["won"])
        self.assertEqual(payload["basic"]["amount"], 20_000)
        self.assertEqual(payload["stake"], 10_000)
        self.assertIn("size", payload)
        self.assertIn("parity", payload)
        self.assertTrue(payload["won"])
        self.assertEqual(payload["popup_title"], "Chúc mừng bạn đã thắng")
        self.assertIn("Trùng 1 số — 20.000 ₫", payload["popup_body"])
        self.assertIn("Cửa Nhỏ — 56.000 ₫", payload["popup_body"])
        self.assertIn("Trúng thưởng", payload["notice_lead"])

    def test_evaluate_sim_popup_lose(self):
        drawn = list(range(1, 11)) + list(range(41, 51))
        payload = evaluate_sim([80], drawn)
        self.assertFalse(payload["won"])
        self.assertEqual(payload["total_amount"], 0)
        self.assertEqual(payload["popup_title"], "Chúc may mắn lần sau")
        self.assertEqual(payload["popup_body"], "")
        self.assertEqual(payload["notice_lead"], "Không trúng · trùng 0 số")

    def test_evaluate_sim_popup_basic_only(self):
        drawn = [1, 41, 42, 43, 44, 45, 2, 3, 4, 5, 46, 47, 6, 7, 8, 9, 10, 48, 49, 50]
        payload = evaluate_sim([1], drawn)
        self.assertTrue(payload["basic"]["won"])
        self.assertFalse(payload["size"]["won"])
        self.assertFalse(payload["parity"]["won"])
        self.assertEqual(payload["popup_title"], "Chúc mừng bạn đã thắng")
        self.assertEqual(payload["popup_body"], "Trùng 1 số — 20.000 ₫.")
        self.assertEqual(payload["notice_lead"], "Trúng thưởng · trùng 1 số · 20.000 ₫")

    def test_evaluate_sim_popup_side_only(self):
        payload = evaluate_sim([80], list(range(1, 21)))
        self.assertFalse(payload["basic"]["won"])
        self.assertTrue(payload["size"]["won"])
        self.assertEqual(payload["popup_title"], "Chúc mừng bạn đã thắng")
        self.assertEqual(payload["popup_body"], "Trùng 0 số. Cửa Nhỏ — 56.000 ₫.")
