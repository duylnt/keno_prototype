from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.content.models import Article, ArticleCategory
from apps.content.views import ARTICLE_LIST_PAGE_SIZE


class InfoHubTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat = ArticleCategory.objects.create(name="Thông tin Keno", slug="thong-tin-keno")
        now = timezone.now()
        cls.lead = Article.objects.create(
            category=cls.cat,
            title="Keno là gì?",
            slug="keno-la-gi",
            excerpt="Keno là xổ số nhanh.",
            body="<p>Keno mở thưởng mỗi 8 phút.</p>",
            is_published=True,
            published_at=now,
        )
        for i in range(1, 6):
            Article.objects.create(
                category=cls.cat,
                title=f"Bài phụ {i}",
                slug=f"bai-phu-{i}",
                excerpt="Tóm tắt bài phụ.",
                body="<p>Nội dung.</p>",
                is_published=True,
                published_at=now - timedelta(hours=i),
            )

    def test_hub_is_news_layout(self):
        r = self.client.get("/thong-tin/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<h1>Thông tin</h1>", html=True)
        self.assertContains(r, "news-masthead")
        self.assertContains(r, "news-sections")
        self.assertContains(r, "news-lead")
        self.assertContains(r, "Keno là gì?")
        self.assertContains(r, "Bài phụ 1")
        self.assertContains(r, "Tin khác")
        self.assertContains(r, "Bài phụ 5")
        self.assertContains(r, "Cách chơi")
        self.assertContains(r, "Chơi thử")
        self.assertContains(r, "Trách nhiệm")
        self.assertContains(r, "Nội quy")
        self.assertContains(r, reverse("content:article_list"))
        self.assertContains(r, reverse("content:how_to_play"))
        self.assertContains(r, reverse("results:simulator"))
        self.assertNotContains(r, "info-hero")
        self.assertNotContains(r, "info-index")
        self.assertNotContains(r, "Các bài viết khác")

    def test_hub_empty_state(self):
        Article.objects.all().delete()
        r = self.client.get("/thong-tin/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Cách chơi")
        self.assertContains(r, "Chưa có bài")
        self.assertNotContains(r, "news-lead")

    def test_desktop_nav_nests_cach_choi_under_thong_tin(self):
        r = self.client.get("/")
        self.assertContains(r, 'href="/thong-tin/"')
        self.assertContains(r, "desk-nav-dd")
        self.assertContains(r, "Thông tin")
        html = r.content.decode()
        how_to = reverse("content:how_to_play")
        self.assertIn(how_to, html)
        self.assertNotIn(f'class="nav-wide" href="{how_to}"', html)
        self.assertIn("tabbar", html)
        self.assertIn("Thông tin", html.split("tabbar", 1)[-1])
        self.assertNotIn("desk-nav-dd-trigger is-active", html)
        self.assertNotIn('class="nav-core is-active" href="/cong-dong/"', html)

    def test_how_to_shares_news_section_bar(self):
        r = self.client.get("/huong-dan/")
        self.assertContains(r, "/thong-tin/")
        self.assertContains(r, "Cách chơi")
        self.assertContains(r, "news-sections")
        self.assertContains(r, 'class="is-on"', html=False)
        self.assertContains(r, "news-kicker")

    def test_article_list_news_archive(self):
        r = self.client.get("/bai-viet/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<h1>Bài viết</h1>", html=True)
        self.assertContains(r, "news-list")
        self.assertContains(r, "Keno là gì?")
        self.assertContains(r, "news-sections")
        self.assertNotContains(r, "Tin & hướng dẫn Keno")

    def test_article_list_paginates(self):
        now = timezone.now()
        for i in range(ARTICLE_LIST_PAGE_SIZE):
            Article.objects.create(
                category=self.cat,
                title=f"Trang hai {i}",
                slug=f"trang-hai-{i}",
                body="<p>x</p>",
                is_published=True,
                published_at=now - timedelta(days=i + 10),
            )
        page1 = self.client.get("/bai-viet/")
        self.assertContains(page1, "Trang 1/")
        self.assertContains(page1, "?trang=2")
        page2 = self.client.get("/bai-viet/?trang=2")
        self.assertEqual(page2.status_code, 200)
        self.assertContains(page2, "Trang 2/")

    def test_article_detail_news_chrome(self):
        r = self.client.get(self.lead.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "news-kicker")
        self.assertContains(r, "Thông tin Keno")
        self.assertContains(r, "<h1>Keno là gì?</h1>", html=True)
        self.assertContains(r, "Tin khác")
        self.assertContains(r, "Bài phụ 1")
        self.assertContains(r, "news-rail")
        self.assertNotContains(r, "Liên kết hữu ích")
        self.assertNotContains(r, "info-page-hero")
