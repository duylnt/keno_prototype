from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from apps.community.facebook import mask_token, sync_facebook_page
from apps.community.models import FacebookPagePost
from apps.core.models import SiteSettings
from apps.locations.auth import POS_OWNER_GROUP, pos_owner_group
from apps.locations.models import ExperienceCode, PosLocation

User = get_user_model()


class FanpageDisplayTests(TestCase):
    def setUp(self):
        self.site = SiteSettings.load()
        self.site.facebook_page_url = "https://www.facebook.com/keno.demo.page"
        self.site.facebook_app_id = "1234567890"
        self.site.facebook_page_id = "111222333"
        self.site.facebook_page_access_token = "EAABsecretTOKEN999xyz"
        self.site.save()

    def test_hub_embeds_page_plugin(self):
        r = self.client.get(reverse("community:hub"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "fb-page")
        self.assertContains(r, "https://www.facebook.com/keno.demo.page")
        self.assertContains(r, "Mở Fanpage")

    def test_token_never_in_html(self):
        r = self.client.get(reverse("community:hub"))
        self.assertNotContains(r, "EAABsecretTOKEN999xyz")
        r2 = self.client.get(reverse("core:live_results"))
        self.assertNotContains(r2, "EAABsecretTOKEN999xyz")

    def test_comments_point_to_fanpage(self):
        r = self.client.get(reverse("core:live_results"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "https://www.facebook.com/keno.demo.page")

    def test_mask_token(self):
        self.assertEqual(mask_token("abcdefghijklmnop"), "abcd••••mnop")
        self.assertEqual(mask_token(""), "")

    def test_sync_without_token(self):
        SiteSettings.objects.filter(pk=1).update(facebook_page_access_token="")
        with override_settings(FACEBOOK_PAGE_ACCESS_TOKEN=""):
            result = sync_facebook_page()
        self.assertFalse(result["ok"])
        self.assertTrue(result["error"])
        self.assertNotIn("EAABsecretTOKEN999xyz", result["error"])

    @patch("apps.community.facebook.graph_request")
    def test_sync_caches_posts(self, mocked):
        mocked.return_value = {
            "data": [
                {
                    "id": "111222333_1",
                    "message": "Kỳ Keno vừa rồi",
                    "created_time": "2026-08-13T02:00:00+0000",
                    "permalink_url": "https://www.facebook.com/111222333_1",
                    "is_hidden": False,
                    "is_published": True,
                }
            ]
        }
        result = sync_facebook_page()
        self.assertTrue(result["ok"])
        self.assertEqual(FacebookPagePost.objects.filter(fb_id="111222333_1").count(), 1)
        r = self.client.get(reverse("community:hub"))
        self.assertContains(r, "Kỳ Keno vừa rồi")


class PartnerPortalTests(TestCase):
    def setUp(self):
        pos_owner_group()
        self.owner_a = User.objects.create_user("chudiem_test", password="keno-pos-2026")
        self.owner_b = User.objects.create_user("chudiem2_test", password="keno-pos-2026")
        self.owner_a.groups.add(Group.objects.get(name=POS_OWNER_GROUP))
        self.owner_b.groups.add(Group.objects.get(name=POS_OWNER_GROUP))
        self.pos_a = PosLocation.objects.create(
            name="POS Alpha Unique",
            address="1 A",
            city="Hà Nội",
            latitude="21.0",
            longitude="105.0",
            owner=self.owner_a,
        )
        self.pos_b = PosLocation.objects.create(
            name="POS Beta Unique",
            address="2 B",
            city="Hồ Chí Minh",
            latitude="10.0",
            longitude="106.0",
            owner=self.owner_b,
        )
        now = timezone.now()
        self.code_a = ExperienceCode.objects.create(
            code="AAA11111",
            expires_at=now + timedelta(days=1),
            redeemed_at=now,
            pos=self.pos_a,
            pos_name=self.pos_a.name,
        )
        self.code_b = ExperienceCode.objects.create(
            code="BBB22222",
            expires_at=now + timedelta(days=1),
            redeemed_at=now,
            pos=self.pos_b,
            pos_name=self.pos_b.name,
        )
        from apps.locations.services import credit_o2o_commission

        credit_o2o_commission(self.code_a)
        credit_o2o_commission(self.code_b)

    def test_anonymous_blocked_from_portal(self):
        r = self.client.get("/doi-tac/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/doi-tac/dang-nhap/", r.url)

    def test_login_alias(self):
        r = self.client.get("/diem-ban/dang-nhap/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Đăng nhập điểm bán")

    def test_owner_cannot_see_other_pos(self):
        self.assertTrue(self.client.login(username="chudiem_test", password="keno-pos-2026"))
        r = self.client.get("/doi-tac/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "POS Alpha Unique")
        self.assertNotContains(r, "POS Beta Unique")
        self.assertNotContains(r, "BBB22222")
        self.assertContains(r, self.code_a.masked_code)
        self.assertContains(r, "5.000")
        self.assertContains(r, "₫")
        self.assertNotContains(r, "mô phỏng")

    def test_staff_partner_login_goes_to_cms(self):
        User.objects.create_superuser("staffcms", "s@keno.local", "keno-admin-2026")
        r = self.client.post(
            "/doi-tac/dang-nhap/",
            {"username": "staffcms", "password": "keno-admin-2026"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.startswith("/cms/"))
