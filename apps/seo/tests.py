from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.content.models import Article, ArticleCategory, ArticleFAQ
from apps.seo.crawler import parse_html
from apps.seo.models import SeoRedirect
from apps.seo.utils import slugify_vi
from apps.seo.writer import generate_article, save_draft, template_draft

User = get_user_model()


class SeoPublicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cat = ArticleCategory.objects.create(name="Thông tin Keno", slug="thong-tin-keno")
        cls.article = Article.objects.create(
            category=cat,
            title="Keno là gì?",
            slug="keno-la-gi",
            excerpt="Keno là xổ số nhanh, mở thưởng mỗi 8 phút.",
            body="<p>Keno là gì? Chọn 1–10 số, kỳ quay 20 số. <a href='/huong-dan/'>Cách chơi</a>.</p>",
            seo_title="Keno là gì?",
            seo_description="Giải thích Keno: xổ số nhanh 8 phút/kỳ, chọn số 01–80.",
            focus_keyword="keno là gì",
            key_takeaways="Keno mở thưởng 8 phút/kỳ.\nKhông bán vé trên website này.",
            is_published=True,
            published_at=timezone.now(),
        )
        ArticleFAQ.objects.create(
            article=cls.article,
            question="Website này có phải Vietlott?",
            answer="Không. Đây là cổng cộng đồng tra cứu.",
        )
        SeoRedirect.objects.create(from_path="/keno/", to_path="/huong-dan/", is_permanent=True)

    def test_robots_allows_ai_bots(self):
        r = self.client.get("/robots.txt")
        self.assertEqual(r.status_code, 200)
        self.assertIn("GPTBot", r.content.decode())
        self.assertIn("ClaudeBot", r.content.decode())
        self.assertIn("PerplexityBot", r.content.decode())
        self.assertIn("Google-Extended", r.content.decode())
        self.assertIn("Allow: /", r.content.decode())
        self.assertIn("Sitemap:", r.content.decode())
        self.assertIn("/llms.txt", r.content.decode())

    def test_llms_txt(self):
        r = self.client.get("/llms.txt")
        self.assertEqual(r.status_code, 200)
        text = r.content.decode()
        self.assertIn("không phải website chính thức", text.lower())
        self.assertIn("/ket-qua/", text)
        self.assertIn("/thong-tin/", text)
        self.assertIn("vietlott", text.lower())

    def test_llms_full_and_wellknown(self):
        full = self.client.get("/llms-full.txt")
        self.assertEqual(full.status_code, 200)
        self.assertIn("Keno là gì?", full.content.decode())
        well = self.client.get("/.well-known/llms.txt")
        self.assertEqual(well.status_code, 200)

    def test_sitemap_index_and_lastmod(self):
        r = self.client.get("/sitemap.xml")
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertIn("sitemapindex", body)
        self.assertIn("sitemap-articles.xml", body)
        self.assertIn("lastmod", body)
        articles = self.client.get("/sitemap-articles.xml")
        self.assertEqual(articles.status_code, 200)
        self.assertIn("keno-la-gi", articles.content.decode())
        self.assertIn("lastmod", articles.content.decode())
        pages = self.client.get("/sitemap-pages.xml")
        self.assertEqual(pages.status_code, 200)
        self.assertIn("/thong-tin/", pages.content.decode())

    def test_canonical_strips_querystring(self):
        r = self.client.get("/thong-ke/?n=30")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'rel="canonical"')
        self.assertContains(r, "/thong-ke/")
        self.assertNotContains(r, "/thong-ke/?n=30")

    def test_home_jsonld(self):
        r = self.client.get("/")
        self.assertContains(r, 'application/ld+json')
        self.assertContains(r, '"Organization"')
        self.assertContains(r, '"WebSite"')
        self.assertContains(r, "không phải website")

    def test_article_jsonld_faq_and_canonical(self):
        r = self.client.get(self.article.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '"Article"')
        self.assertContains(r, '"FAQPage"')
        self.assertContains(r, '"BreadcrumbList"')
        self.assertContains(r, 'rel="canonical"')
        self.assertContains(r, self.article.slug)

    def test_howto_schema(self):
        r = self.client.get("/huong-dan/")
        self.assertContains(r, '"HowTo"')
        self.assertContains(r, '"FAQPage"')

    def test_redirect_301(self):
        r = self.client.get("/keno/", follow=False)
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r["Location"], "/huong-dan/")

    def test_og_twitter_and_llms_link(self):
        r = self.client.get("/")
        self.assertContains(r, 'property="og:title"')
        self.assertContains(r, 'name="twitter:title"')
        self.assertContains(r, "llms.txt")

    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_404_page(self):
        r = self.client.get("/trang-khong-ton-tai-seo/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "Không tìm thấy trang", status_code=404)
        self.assertContains(r, "Trang chủ", status_code=404)


class CrawlerParserTests(TestCase):
    def test_parse_html_extracts_metadata_not_full_copy(self):
        html = """
        <html><head>
          <title>Cách chơi Keno</title>
          <meta name="description" content="Hướng dẫn Keno">
          <link rel="canonical" href="https://example.com/keno">
          <script type="application/ld+json">{"@type":"Article"}</script>
        </head><body>
          <h1>Cách chơi Keno</h1>
          <h2>Chọn số</h2>
          <p>{"x" * 20} đoạn dài hơn bốn trăm ký tự. """ + ("keno " * 80) + """</p>
        </body></html>
        """
        data = parse_html(html, "https://example.com/keno")
        self.assertEqual(data["title"], "Cách chơi Keno")
        self.assertIn("Hướng dẫn", data["meta_description"])
        self.assertEqual(data["canonical"], "https://example.com/keno")
        self.assertTrue(any(h["tag"] == "h1" for h in data["headings"]))
        self.assertLessEqual(len(data["excerpt"]), 400)
        self.assertIn("Article", data["schema_types"])
        self.assertEqual(data["product_hint"], "keno")


class WriterTests(TestCase):
    def test_template_draft_is_vietnamese_and_responsible(self):
        draft = template_draft("Cách đọc thống kê Keno")
        self.assertIn("trách nhiệm", draft["body_html"].lower())
        self.assertNotIn("chắc thắng", draft["body_html"].lower())
        self.assertTrue(draft["faqs"])
        self.assertLessEqual(len(draft["seo_title"]), 70)

    def test_save_draft_never_publishes(self):
        ArticleCategory.objects.create(name="Thông tin Keno", slug="thong-tin-keno")
        draft = generate_article("Keno khác Mega 6/45 như thế nào?")
        article = save_draft(draft)
        self.assertFalse(article.is_published)
        self.assertTrue(article.robots_noindex)
        self.assertTrue(article.faqs.exists())

    def test_slugify_vi(self):
        self.assertEqual(slugify_vi("Keno là gì?"), "keno-la-gi")


class SeoCmsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "a@b.c", "x")
        self.client.force_login(self.user)

    def test_toolbox_and_writer_pages(self):
        self.assertEqual(self.client.get(reverse("admin:seo_toolbox")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:seo_research")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:seo_writer")).status_code, 200)

    def test_writer_saves_draft(self):
        ArticleCategory.objects.create(name="Thông tin Keno", slug="thong-tin-keno")
        r = self.client.post(
            reverse("admin:seo_writer"),
            {"topic": "Keno là gì cho người mới", "save": "1"},
        )
        self.assertEqual(r.status_code, 302)
        article = Article.objects.get(is_published=False)
        self.assertTrue(article.robots_noindex)
