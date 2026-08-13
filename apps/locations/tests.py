from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from apps.core.models import SiteSettings
from apps.locations.auth import pos_owner_group
from apps.locations.models import POS_OWNER_GROUP, ExperienceCode, OwnerWallet, PosLocation
from apps.locations.services import commission_amounts, credit_o2o_commission, request_payout

User = get_user_model()


class CommissionWalletTests(TestCase):
    def setUp(self):
        pos_owner_group()
        self.owner = User.objects.create_user("wallet_owner", password="keno-pos-2026")
        self.pos = PosLocation.objects.create(
            name="POS Wallet",
            address="3 C",
            city="Đà Nẵng",
            latitude="16.0",
            longitude="108.0",
            owner=self.owner,
        )
        site = SiteSettings.load()
        site.o2o_commission_type = SiteSettings.COMMISSION_FIXED
        site.o2o_commission_rate = 5000
        site.wallet_vnd_per_point = 1000
        site.save()

    def test_redeem_credits_wallet_once(self):
        code = ExperienceCode.objects.create(
            code="WALLET01",
            expires_at=timezone.now() + timedelta(days=1),
            redeemed_at=timezone.now(),
            pos=self.pos,
            pos_name=self.pos.name,
        )
        amount, points = commission_amounts()
        self.assertEqual(amount, 5000)
        self.assertEqual(points, 5)
        first = credit_o2o_commission(code)
        second = credit_o2o_commission(code)
        self.assertEqual(first.pk, second.pk)
        wallet = OwnerWallet.objects.get(user=self.owner)
        self.assertEqual(wallet.points_balance, 5)
        request_payout(self.owner, 5)
        wallet.refresh_from_db()
        self.assertEqual(wallet.points_balance, 0)


class PartnerLoginTests(TestCase):
    def setUp(self):
        pos_owner_group()
        self.owner = User.objects.create_user(
            "chudiem",
            email="chudiem@keno.local",
            password="keno-pos-2026",
        )
        self.owner.groups.add(Group.objects.get(name=POS_OWNER_GROUP))
        PosLocation.objects.create(
            name="Điểm bán Keno Hoàn Kiếm",
            address="18 Lương Văn Can",
            district="Hoàn Kiếm",
            city="Hà Nội",
            latitude="21.028511",
            longitude="105.854444",
            owner=self.owner,
        )

    def test_login_page_has_no_demo_cheat_sheet(self):
        r = self.client.get("/doi-tac/dang-nhap/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'name="username"')
        self.assertContains(r, 'name="password"')
        self.assertNotContains(r, "chudiem")
        self.assertNotContains(r, "keno-pos-2026")
        self.assertNotContains(r, "Nhân viên CMS")
        self.assertNotContains(r, "Demo:")
        self.assertNotContains(r, "Cổng đối tác:")

    def test_demo_login_reaches_dashboard(self):
        user = authenticate(username="chudiem", password="keno-pos-2026")
        self.assertIsNotNone(user)
        r = self.client.post(
            "/doi-tac/dang-nhap/",
            {"username": "chudiem", "password": "keno-pos-2026"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, "/doi-tac/")
        dash = self.client.get("/doi-tac/")
        self.assertEqual(dash.status_code, 200)
        self.assertContains(dash, "Điểm bán Keno Hoàn Kiếm")
        self.assertContains(dash, "18 Lương Văn Can, Hoàn Kiếm, Hà Nội")
        self.assertNotContains(dash, "partner-pos-addr")
        self.assertNotContains(dash, "<th>Điểm bán</th>")

    def test_wrong_password_message(self):
        r = self.client.post(
            "/doi-tac/dang-nhap/",
            {"username": "chudiem", "password": "sai-mat-khau"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Sai mật khẩu")

    def test_unknown_user_message(self):
        r = self.client.post(
            "/doi-tac/dang-nhap/",
            {"username": "khongco", "password": "keno-pos-2026"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Không tìm thấy tài khoản")
        self.assertNotContains(r, "chudiem")
        self.assertNotContains(r, "keno-pos-2026")
        self.assertNotContains(r, "Demo:")

    def test_no_permission_message(self):
        User.objects.create_user("khach", password="keno-pos-2026")
        r = self.client.post(
            "/doi-tac/dang-nhap/",
            {"username": "khach", "password": "keno-pos-2026"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "chưa được gán làm chủ điểm bán")

    def test_formatted_address_joins_parts(self):
        pos = PosLocation(
            name="Điểm bán Keno Hoàn Kiếm",
            address="18 Lương Văn Can",
            district="Hoàn Kiếm",
            city="Hà Nội",
            latitude="21.028511",
            longitude="105.854444",
        )
        self.assertEqual(pos.formatted_address, "18 Lương Văn Can, Hoàn Kiếm, Hà Nội")

    def test_header_lists_extra_pos_address(self):
        PosLocation.objects.create(
            name="Điểm bán Keno Cầu Giấy",
            address="32 Trần Thái Tông",
            district="Cầu Giấy",
            city="Hà Nội",
            latitude="21.033333",
            longitude="105.792778",
            owner=self.owner,
        )
        self.client.force_login(self.owner)
        dash = self.client.get("/doi-tac/")
        self.assertContains(dash, "18 Lương Văn Can, Hoàn Kiếm, Hà Nội")
        self.assertContains(dash, "32 Trần Thái Tông, Cầu Giấy, Hà Nội")
        self.assertContains(dash, "+1 điểm")

    def test_scan_table_omits_repeated_address(self):
        pos = PosLocation.objects.get(name="Điểm bán Keno Hoàn Kiếm")
        ExperienceCode.objects.create(
            code="SCAN01",
            expires_at=timezone.now() + timedelta(days=1),
            redeemed_at=timezone.now(),
            pos=pos,
            pos_name=pos.name,
        )
        self.client.force_login(self.owner)
        dash = self.client.get("/doi-tac/")
        self.assertContains(dash, "Mã đã quét tại cửa hàng")
        self.assertContains(dash, "SC•••01")
        html = dash.content.decode()
        addr = "18 Lương Văn Can, Hoàn Kiếm, Hà Nội"
        self.assertEqual(html.count(addr), 1)
        self.assertNotIn("partner-pos-addr", html)

    def test_dashboard_formats_vnd_and_hides_demo_copy(self):
        pos = PosLocation.objects.get(name="Điểm bán Keno Hoàn Kiếm")
        code = ExperienceCode.objects.create(
            code="SCAN02",
            expires_at=timezone.now() + timedelta(days=1),
            redeemed_at=timezone.now(),
            pos=pos,
            pos_name=pos.name,
        )
        credit_o2o_commission(code)
        self.client.force_login(self.owner)
        dash = self.client.get("/doi-tac/")
        html = dash.content.decode()
        self.assertIn("5.000", html)
        self.assertIn("₫", html)
        self.assertIn('class="vnd money"', html)
        self.assertIn("partner-kpi-chip", html)
        self.assertNotIn("5000 đ", html)
        self.assertNotIn("mô phỏng", html)
        self.assertNotIn("không phải thanh toán thật", html)
        self.assertNotIn("chudiem", html)
        self.assertNotIn("keno-pos-2026", html)


class VndFilterTests(TestCase):
    def render(self, value):
        from django.template import Context, Template

        tpl = Template("{% load money %}{{ value|vnd }}")
        return tpl.render(Context({"value": value}))

    def test_zero(self):
        html = self.render(0)
        self.assertIn(">0<", html)
        self.assertIn("₫", html)
        self.assertIn('class="vnd money"', html)
        self.assertIn("\xa0", html)

    def test_thousands_dot(self):
        html = self.render(5000)
        self.assertIn("5.000", html)
        self.assertNotIn("5,000", html)
        self.assertNotIn("5000", html)

    def test_invalid_is_zero(self):
        html = self.render("")
        self.assertIn(">0<", html)
