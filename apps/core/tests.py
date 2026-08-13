from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.content.models import StaticPage
from apps.core.nav import nav_on, path_under
from apps.results.services import ensure_draws_up_to_now


class NavMatchingTests(TestCase):
    def test_slash_does_not_match_everything(self):
        self.assertFalse(path_under("/", "/ket-qua/"))
        self.assertFalse(path_under("/ket-qua/", "/"))
        flags = nav_on("/")
        self.assertFalse(any(flags.values()))

    def test_results_does_not_steal_live(self):
        self.assertTrue(nav_on("/ket-qua/")["results"])
        self.assertTrue(nav_on("/ket-qua/hom-nay/")["results"])
        self.assertTrue(nav_on("/ket-qua/lich-su/")["results"])
        live = nav_on("/ket-qua-truc-tiep/")
        self.assertTrue(live["live"])
        self.assertFalse(live["results"])
        self.assertFalse(nav_on("/truc-tiep/")["results"])

    def test_community_excludes_guidelines(self):
        hub = nav_on("/cong-dong/")
        self.assertTrue(hub["community"])
        self.assertFalse(hub["info"])
        join = nav_on("/cong-dong/tham-gia/")
        self.assertTrue(join["community"])
        self.assertFalse(join["info"])
        rules = nav_on("/cong-dong/noi-quy/")
        self.assertFalse(rules["community"])
        self.assertTrue(rules["info"])
        self.assertTrue(rules["info_guidelines"])

    def test_info_pages_only(self):
        for path in (
            "/thong-tin/",
            "/bai-viet/",
            "/bai-viet/keno-la-gi/",
            "/huong-dan/",
            "/choi-thu/",
            "/trang/choi-co-trach-nhiem/",
        ):
            flags = nav_on(path)
            self.assertTrue(flags["info"], path)
            self.assertFalse(flags["community"], path)
            self.assertFalse(flags["results"], path)

    def test_stats_check_locations(self):
        self.assertTrue(nav_on("/thong-ke/")["stats"])
        self.assertTrue(nav_on("/thong-ke/lon-nho/")["stats"])
        self.assertTrue(nav_on("/do-ve/")["check"])
        self.assertTrue(nav_on("/diem-ban/")["locations"])
        self.assertTrue(nav_on("/diem-ban/12/")["locations"])
        self.assertFalse(nav_on("/diem-ban/dang-nhap/")["locations"])
        self.assertFalse(nav_on("/thong-ke/")["info"])
        self.assertFalse(nav_on("/do-ve/")["community"])


class PublicNavHighlightTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ensure_draws_up_to_now(lookback_days=0)
        StaticPage.objects.get_or_create(
            slug="choi-co-trach-nhiem",
            defaults={"title": "Chơi có trách nhiệm", "body": "<p>x</p>", "is_published": True},
        )

    def _html(self, path):
        r = self.client.get(path)
        self.assertEqual(r.status_code, 200, path)
        return r.content.decode()

    def test_home_highlights_nothing(self):
        html = self._html("/")
        self.assertNotIn("desk-nav-dd-trigger is-active", html)
        self.assertNotIn('class="nav-core is-active"', html)
        self.assertNotIn("live-tab--desk is-active", html)
        tab = html.split('class="tabbar', 1)[-1]
        self.assertNotIn('class="is-active"', tab)
        self.assertNotIn("live-tab--tabbar is-active", html)

    def test_info_hub_only_thong_tin(self):
        html = self._html("/thong-tin/")
        self.assertIn("desk-nav-dd-trigger is-active", html)
        self.assertNotIn('class="nav-core is-active" href="/cong-dong/"', html)
        self.assertIn('href="/thong-tin/" class="is-active" aria-current="page"', html)
        self.assertNotIn('href="/cong-dong/" class="is-active"', html)
        self.assertNotIn("<span>ⓘ</span>", html)

    def test_community_hub_only_cong_dong(self):
        html = self._html("/cong-dong/")
        self.assertIn('class="nav-core is-active" href="/cong-dong/"', html)
        self.assertNotIn("desk-nav-dd-trigger is-active", html)
        self.assertIn('href="/cong-dong/" class="is-active" aria-current="page"', html)
        self.assertNotIn('href="/thong-tin/" class="is-active"', html)

    def test_guidelines_is_info_not_community(self):
        html = self._html("/cong-dong/noi-quy/")
        self.assertIn("desk-nav-dd-trigger is-active", html)
        self.assertNotIn('class="nav-core is-active" href="/cong-dong/"', html)
        self.assertIn('href="/thong-tin/" class="is-active" aria-current="page"', html)
        self.assertNotIn('href="/cong-dong/" class="is-active"', html)

    def test_live_not_ket_qua(self):
        html = self._html(reverse("core:live_results"))
        self.assertIn("live-tab--desk is-active", html)
        self.assertIn("live-tab--tabbar is-active", html)
        self.assertNotIn('class="nav-core is-active" href="/ket-qua/"', html)
        self.assertNotIn("desk-nav-dd-trigger is-active", html)

    def test_results_not_live(self):
        html = self._html("/ket-qua/")
        self.assertIn('class="nav-core is-active" href="/ket-qua/"', html)
        self.assertNotIn("live-tab--desk is-active", html)
        self.assertNotIn("desk-nav-dd-trigger is-active", html)

    def test_nested_info_pages(self):
        for path in ("/huong-dan/", "/choi-thu/", "/trang/choi-co-trach-nhiem/"):
            html = self._html(path)
            self.assertIn("desk-nav-dd-trigger is-active", html)
            self.assertNotIn('class="nav-core is-active" href="/cong-dong/"', html)

    def test_context_processor_matches_helper(self):
        request = RequestFactory().get("/thong-tin/")
        from apps.core.context_processors import site_chrome

        ctx = site_chrome(request)
        self.assertEqual(ctx["nav_on"], nav_on("/thong-tin/"))
