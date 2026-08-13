"""Seed CMS content, simulated draws, POS, community and sample KPI data."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.models import (
    AnalyticsEvent,
    CommunityKpiSnapshot,
    DailyMetric,
    GA4Snapshot,
    GSCQuery,
    GSCSnapshot,
    TechnicalKpiSnapshot,
)
from apps.community.models import (
    BannedKeyword,
    CommunityGuideline,
    CommunityPost,
    JoinQuestion,
    MinigameEvent,
)
from apps.content.models import Article, ArticleCategory, ArticleFAQ, StaticPage
from apps.core.models import Banner, SiteSettings
from apps.locations.auth import pos_owner_group
from apps.locations.models import ExperienceCode, PosLocation
from apps.locations.services import credit_o2o_commission
from apps.results.services import ensure_draws_up_to_now
from apps.seo.crawler import persist_result
from apps.seo.models import SeoRedirect
from apps.seo.sample_market import SAMPLE_MARKET

User = get_user_model()


ARTICLES = [
    (
        "ket-qua",
        "Kết quả Keno hôm nay — tra cứu theo từng kỳ 8 phút",
        "ket-qua-keno-hom-nay",
        "Xem kết quả Keno hôm nay, kỳ mới nhất và lịch sử trong ngày trên giao diện mobile.",
        "<p>Keno mở thưởng liên tục mỗi 8 phút từ 06:00 đến 21:52. Trang kết quả giúp bạn theo dõi kỳ mới nhất, đếm ngược kỳ tiếp theo và xem lại các kỳ trong ngày.</p>",
    ),
    (
        "ket-qua",
        "Kết quả Keno kỳ mới nhất",
        "ket-qua-keno-ky-moi-nhat",
        "Cập nhật kết quả kỳ Keno mới nhất kèm 20 số, Lớn/Nhỏ và Chẵn/Lẻ.",
        "<p>Mỗi kỳ Keno quay 20 số từ 01 đến 80. Ngoài dãy số, bạn có thể xem tổng, Lớn/Nhỏ và Chẵn/Lẻ của kỳ đó.</p>",
    ),
    (
        "ket-qua",
        "Lịch sử kết quả Keno",
        "lich-su-ket-qua-keno",
        "Tra cứu lịch sử các kỳ quay Keno theo ngày.",
        "<p>Lịch sử kết quả giúp người chơi đối chiếu vé và theo dõi chuỗi kỳ quay. Hãy dùng bộ lọc theo ngày để xem đúng phiên bạn cần.</p>",
    ),
    (
        "thong-tin",
        "Keno là gì?",
        "keno-la-gi",
        "Keno là sản phẩm xổ số nhanh của Vietlott, mở thưởng mỗi 8 phút.",
        "<p><strong>Keno</strong> là sản phẩm xổ số nhanh với tần suất mở thưởng 8 phút/kỳ, từ 06:00 đến 21:52 hàng ngày. Người chơi chọn từ 1 đến 10 số trong dải 01–80; mỗi kỳ quay ra 20 số.</p><p>Keno chỉ được phân phối tại các điểm bán chính thức — website này không bán vé trực tuyến mà hỗ trợ tra cứu, tìm hiểu và tìm điểm bán gần bạn.</p>",
    ),
    (
        "thong-tin",
        "Cách chơi Keno",
        "cach-choi-keno",
        "Hướng dẫn cách chọn số, các hình thức cược Lớn/Nhỏ Chẵn/Lẻ và kiểm tra kết quả.",
        "<h2>Chọn số</h2><p>Bạn chọn 1–10 số từ 01 đến 80. Kỳ quay sẽ ra 20 số. Số lượng số trùng khớp quyết định mức thưởng theo bảng công bố tại điểm bán.</p><h2>Lớn / Nhỏ</h2><p>Dựa trên tổng 20 số quay: Nhỏ (210–810), Lớn (811–1410). Đây là thông tin mô tả sản phẩm, không phải công cụ dự đoán.</p><h2>Chẵn / Lẻ</h2><p>Dựa trên số lượng số chẵn trong 20 số: Chẵn (≥11 số chẵn), Lẻ (≥11 số lẻ), Hòa (10–10).</p><p>Hãy chơi có trách nhiệm. Không chơi quá khả năng tài chính.</p>",
    ),
    (
        "thong-tin",
        "Cơ cấu giải thưởng Keno",
        "co-cau-giai-thuong-keno",
        "Tìm hiểu cơ chế trả thưởng Keno theo số lượng số chọn và số trùng.",
        "<p>Cơ cấu giải thưởng Keno phụ thuộc vào số lượng số bạn chọn và số lượng số trùng với kết quả kỳ quay. Bảng trả thưởng chính thức được niêm yết tại điểm bán và trên kênh Vietlott.</p><p>Website không đưa ra cam kết trúng thưởng hay hàm ý kiểm soát kết quả.</p>",
    ),
    (
        "thong-tin",
        "Hướng dẫn kiểm tra kết quả vé Keno",
        "huong-dan-kiem-tra-ket-qua",
        "Cách dò vé Keno trên web: nhập mã kỳ và dãy số đã chọn.",
        "<p>Vào mục <strong>Dò vé</strong>, chọn kỳ quay (hoặc dùng kỳ mới nhất), nhập 1–10 số trên vé rồi kiểm tra số trùng. Công cụ chỉ đối chiếu dữ liệu kết quả, không thay thế xác nhận tại điểm bán.</p>",
    ),
    (
        "du-lieu",
        "Thống kê kết quả các kỳ quay Keno",
        "thong-ke-ket-qua-keno",
        "Xem tần suất xuất hiện, nóng/lạnh — dữ liệu tham khảo, không dự đoán kết quả.",
        "<p>Thống kê tần suất giúp quan sát dữ liệu lịch sử. <strong>Thống kê không phải công cụ dự đoán</strong> và không làm tăng khả năng trúng.</p>",
    ),
    (
        "du-lieu",
        "Lịch sử Lớn / Nhỏ Keno",
        "lich-su-lon-nho-keno",
        "Chuỗi Lớn/Nhỏ các kỳ quay gần nhất.",
        "<p>Trang Lớn/Nhỏ hiển thị chuỗi kết quả theo tổng 20 số. Dùng để theo dõi, không dùng để “bắt cầu” hay cam kết kỳ tới.</p>",
    ),
    (
        "du-lieu",
        "Lịch sử Chẵn / Lẻ Keno",
        "lich-su-chan-le-keno",
        "Chuỗi Chẵn/Lẻ/Hòa các kỳ quay gần nhất.",
        "<p>Chẵn/Lẻ được tính theo số lượng số chẵn trong 20 số quay. Hòa xảy ra khi đúng 10 số chẵn và 10 số lẻ.</p>",
    ),
    (
        "cong-dong",
        "Cộng đồng người chơi Keno — quán cà phê online",
        "cong-dong-nguoi-choi-keno",
        "Không gian thảo luận lành mạnh: kết quả, kiến thức, dữ liệu và minigame.",
        "<p>Cộng đồng Keno được định vị như quán cà phê online: cập nhật kỳ quay, chia sẻ trải nghiệm, thảo luận văn minh. Không bán số, không môi giới, không spam.</p>",
    ),
]


POS = [
    ("Điểm bán Keno Hoàn Kiếm", "18 Lương Văn Can", "Hoàn Kiếm", "Hà Nội", 21.028511, 105.854444, "024 1234 0101"),
    ("Điểm bán Keno Cầu Giấy", "32 Trần Thái Tông", "Cầu Giấy", "Hà Nội", 21.033333, 105.792778, "024 1234 0102"),
    ("Điểm bán Keno Đống Đa", "110 Tây Sơn", "Đống Đa", "Hà Nội", 21.013056, 105.827222, "024 1234 0103"),
    ("Điểm bán Keno Quận 1", "45 Nguyễn Huệ", "Quận 1", "TP. Hồ Chí Minh", 10.776889, 106.700806, "028 1234 0201"),
    ("Điểm bán Keno Quận 3", "22 Võ Văn Tần", "Quận 3", "TP. Hồ Chí Minh", 10.782778, 106.689444, "028 1234 0202"),
    ("Điểm bán Keno Tân Bình", "18 Hoàng Văn Thụ", "Tân Bình", "TP. Hồ Chí Minh", 10.799167, 106.659444, "028 1234 0203"),
    ("Điểm bán Keno Hải Châu", "36 Trần Phú", "Hải Châu", "Đà Nẵng", 16.067778, 108.220833, "0236 123 0301"),
    ("Điểm bán Keno Thanh Khê", "12 Điện Biên Phủ", "Thanh Khê", "Đà Nẵng", 16.066944, 108.187500, "0236 123 0302"),
    ("Điểm bán Keno Ninh Kiều", "01 Hòa Bình", "Ninh Kiều", "Cần Thơ", 10.034167, 105.788333, "0292 123 0401"),
    ("Điểm bán Keno Thủ Dầu Một", "88 Yersin", "Thủ Dầu Một", "Bình Dương", 10.980000, 106.651944, "0274 123 0501"),
]


class Command(BaseCommand):
    help = "Tạo dữ liệu demo + tài khoản CMS (admin / keno-admin-2026)."

    def handle(self, *args, **options):
        self._user()
        # POS owners first so /doi-tac/ login works even if later seed steps fail.
        self._pos()
        self._settings()
        self._banners()
        self._content()
        self._community()
        created = ensure_draws_up_to_now(lookback_days=3)
        self.stdout.write(f"Kỳ quay mô phỏng: +{created}")
        self._analytics()
        self.stdout.write(self.style.SUCCESS("seed_demo hoàn tất."))
        self.stdout.write("CMS: http://127.0.0.1:8000/cms/  |  user=admin  pass=keno-admin-2026")
        self.stdout.write("Điểm bán: http://127.0.0.1:8000/doi-tac/dang-nhap/  |  user=chudiem  pass=keno-pos-2026")

    def _user(self):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@keno.local", "keno-admin-2026")
            self.stdout.write("Đã tạo superuser admin")
        else:
            self.stdout.write("Superuser admin đã tồn tại")

    def _settings(self):
        s = SiteSettings.load()
        s.site_name = "Keno"
        s.tagline = "Tra cứu kết quả · Cộng đồng · Điểm bán gần bạn"
        s.facebook_group_url = "https://www.facebook.com/groups/"
        s.facebook_group_name = "Cộng đồng người chơi Keno"
        s.facebook_page_url = s.facebook_page_url or ""
        s.facebook_page_id = s.facebook_page_id or ""
        s.zalo_group_url = s.zalo_group_url or ""
        s.community_cta_label = "Mở Fanpage"
        s.o2o_commission_type = SiteSettings.COMMISSION_FIXED
        s.o2o_commission_rate = 5000
        s.o2o_commission_base_vnd = 10000
        s.wallet_vnd_per_point = 1000
        s.facebook_moderation_roles = s.facebook_moderation_roles or "Admin Page duyệt bài; Moderator trả lời inbox."
        s.support_note = "Keno chỉ mua tại điểm bán chính thức."
        s.save()

    def _banners(self):
        Banner.objects.get_or_create(
            title="Tìm điểm bán Keno gần bạn",
            defaults={
                "subtitle": "Mở bản đồ điểm bán",
                "link_url": "/diem-ban/",
                "placement": Banner.PLACEMENT_HOME,
                "sort_order": 1,
            },
        )
        Banner.objects.get_or_create(
            title="Quán cà phê Keno online",
            defaults={
                "subtitle": "Thảo luận văn minh, không bán số, không spam",
                "link_url": "/cong-dong/",
                "placement": Banner.PLACEMENT_COMMUNITY,
                "sort_order": 1,
            },
        )

    def _content(self):
        cats = {
            "ket-qua": ("Kết quả mở thưởng", "ket-qua-mo-thuong", "Kết quả Keno, kỳ mới nhất, lịch sử."),
            "thong-tin": ("Thông tin Keno", "thong-tin-keno", "Keno là gì, cách chơi, cơ cấu giải."),
            "du-lieu": ("Dữ liệu Keno", "du-lieu-keno", "Thống kê, Lớn/Nhỏ, Chẵn/Lẻ."),
            "cong-dong": ("Keno Community", "keno-community", "Chủ đề thảo luận và trải nghiệm."),
        }
        cat_objs = {}
        for i, (key, (name, slug, desc)) in enumerate(cats.items(), start=1):
            cat_objs[key], _ = ArticleCategory.objects.get_or_create(
                slug=slug, defaults={"name": name, "description": desc, "sort_order": i}
            )
        now = timezone.now()
        for i, (cat, title, slug, excerpt, body) in enumerate(ARTICLES):
            Article.objects.get_or_create(
                slug=slug,
                defaults={
                    "category": cat_objs[cat],
                    "title": title,
                    "excerpt": excerpt,
                    "body": body,
                    "seo_title": title[:70],
                    "seo_description": excerpt[:160],
                    "published_at": now - timedelta(days=len(ARTICLES) - i),
                },
            )
        StaticPage.objects.get_or_create(
            slug="cach-choi-keno",
            defaults={
                "title": "Cách chơi Keno",
                "body": ARTICLES[4][4],
                "seo_title": "Cách chơi Keno",
                "seo_description": "Hướng dẫn sản phẩm Keno dành cho người mới.",
            },
        )
        StaticPage.objects.get_or_create(
            slug="choi-co-trach-nhiem",
            defaults={
                "title": "Chơi có trách nhiệm",
                "body": (
                    "<p>Keno là sản phẩm giải trí. Không chơi quá khả năng tài chính, "
                    "không xem thống kê như công cụ dự đoán, không tin lời hứa trúng chắc.</p>"
                    "<p>Nếu bạn hoặc người thân có dấu hiệu chơi quá mức, hãy dừng lại và tìm hỗ trợ.</p>"
                ),
                "seo_title": "Chơi có trách nhiệm | Keno",
                "seo_description": "Keno là giải trí. Không chơi quá khả năng tài chính, không tin cam kết trúng thưởng.",
                "excerpt": "Nguyên tắc chơi có trách nhiệm trên cổng cộng đồng Keno.",
            },
        )
        self._seo_enrich()

    def _seo_enrich(self):
        links = (
            '<p>Xem thêm: <a href="/ket-qua/">kết quả Keno</a>, '
            '<a href="/huong-dan/">cách chơi</a>, '
            '<a href="/thong-ke/">thống kê</a>, '
            '<a href="/diem-ban/">điểm bán gần bạn</a>.</p>'
        )
        keywords = {
            "ket-qua-keno-hom-nay": "kết quả keno",
            "ket-qua-keno-ky-moi-nhat": "kết quả keno",
            "lich-su-ket-qua-keno": "lịch sử keno",
            "keno-la-gi": "keno là gì",
            "cach-choi-keno": "cách chơi keno",
            "co-cau-giai-thuong-keno": "giải thưởng keno",
            "huong-dan-kiem-tra-ket-qua": "dò vé keno",
            "thong-ke-ket-qua-keno": "thống kê keno",
            "lich-su-lon-nho-keno": "lớn nhỏ keno",
            "lich-su-chan-le-keno": "chẵn lẻ keno",
            "cong-dong-nguoi-choi-keno": "cộng đồng keno",
        }
        faqs = {
            "keno-la-gi": [
                ("Keno là gì?", "Keno là xổ số nhanh: mỗi kỳ quay 20 số từ 01–80; người chơi chọn 1–10 số. Mở thưởng mỗi 8 phút."),
                ("Có phải website chính thức Vietlott?", "Không. Đây là cổng cộng đồng tra cứu, không bán vé trực tuyến."),
            ],
            "cach-choi-keno": [
                ("Chơi Keno như thế nào?", "Chọn 1–10 số hoặc cửa Lớn/Nhỏ Chẵn/Lẻ, mua vé tại điểm bán, đối chiếu kết quả kỳ quay."),
                ("Mua vé online được không?", "Không trên website này. Chỉ mua tại điểm bán chính thức."),
            ],
            "thong-ke-ket-qua-keno": [
                ("Thống kê có giúp trúng không?", "Không. Thống kê chỉ mô tả dữ liệu quá khứ."),
            ],
        }
        for article in Article.objects.all():
            changed = []
            kw = keywords.get(article.slug)
            if kw and not article.focus_keyword:
                article.focus_keyword = kw
                changed.append("focus_keyword")
            if not article.key_takeaways and article.excerpt:
                article.key_takeaways = (
                    f"{article.excerpt}\n"
                    "Vé Keno chỉ bán tại điểm bán chính thức.\n"
                    "Thống kê không phải công cụ dự đoán."
                )
                changed.append("key_takeaways")
            if article.body and 'href="/' not in article.body:
                article.body = article.body + links
                changed.append("body")
            if not article.author_name:
                article.author_name = "Ban biên tập Keno"
                changed.append("author_name")
            if changed:
                article.save(update_fields=changed)
            for i, (q, a) in enumerate(faqs.get(article.slug, [])):
                ArticleFAQ.objects.get_or_create(
                    article=article, question=q, defaults={"answer": a, "sort_order": i}
                )
        SeoRedirect.objects.get_or_create(
            from_path="/keno/",
            defaults={"to_path": "/huong-dan/", "note": "Alias cách chơi", "is_permanent": True},
        )
        from apps.seo.models import ResearchUrl

        if not ResearchUrl.objects.exists():
            now = timezone.now()
            for row in SAMPLE_MARKET:
                persist_result({**row, "robots_allowed": True, "fetched_at": now}, row["product_hint"])

    def _community(self):
        rules = [
            ("Không bán số, môi giới hoặc lừa đảo", "<p>Nghiêm cấm mọi hình thức bán số, cầm hộ, môi giới trái phép.</p>"),
            ("Không cam kết trúng thưởng", "<p>Không đăng nội dung hàm ý dự đoán chắc chắn hoặc kiểm soát kết quả.</p>"),
            ("Thảo luận văn minh", "<p>Tôn trọng người khác. Không spam, không công kích.</p>"),
            ("Chơi có trách nhiệm", "<p>Không khuyến khích chơi quá mức. Cộng đồng là nơi chia sẻ, không phải nơi thúc đẩy cược.</p>"),
        ]
        for i, (title, body) in enumerate(rules, start=1):
            CommunityGuideline.objects.get_or_create(title=title, defaults={"body": body, "sort_order": i})
        questions = [
            ("Bạn tham gia nhóm để làm gì?", "Tra cứu / thảo luận / tìm hiểu sản phẩm — không phải để mua số."),
            ("Bạn cam kết không bán số hoặc môi giới?", "Có, tôi cam kết tuân thủ nội quy."),
            ("Bạn đã đọc nội quy cộng đồng chưa?", "Đã đọc và đồng ý."),
        ]
        for i, (q, hint) in enumerate(questions, start=1):
            JoinQuestion.objects.get_or_create(question=q, defaults={"hint": hint, "sort_order": i})
        for kw in ["bán số", "ban so", "cầm hộ", "cam ho", "lô đề", "chắc trúng", "soi cầu", "vip number"]:
            BannedKeyword.objects.get_or_create(keyword=kw, defaults={"reason": "Spam / bán số / dự đoán chắc"})
        posts = [
            ("Kỳ trưa nay nhịp 8 phút quá nhanh!", "Ai cũng canh countdown không?", "realtime", 24, True),
            ("Keno là gì — giải thích cho bạn mới", "Tóm tắt: chọn 1–10 số, quay 20 số, mua tại điểm bán.", "knowledge", 18, True),
            ("Nhìn thống kê thế nào cho đúng?", "Thống kê để xem dữ liệu, không phải để bắt cầu.", "data", 31, True),
            ("Chia sẻ trải nghiệm tìm điểm bán gần nhà", "Mình dùng GPS xong chỉ đường rất tiện.", "community", 12, True),
            ("Minigame cuối tuần trên group", "Hoạt động đã được duyệt nội bộ, phần thưởng là thẻ cà phê — không gắn với kết quả kỳ quay.", "entertainment", 40, False),
        ]
        now = timezone.now()
        for i, (title, body, pillar, comments, feat) in enumerate(posts):
            CommunityPost.objects.get_or_create(
                title=title,
                defaults={
                    "body": body,
                    "author_name": "Điều phối viên",
                    "pillar": pillar,
                    "status": CommunityPost.STATUS_APPROVED,
                    "is_featured": feat,
                    "comment_count": comments,
                    "created_at": now - timedelta(hours=i * 5),
                    "moderated_at": now,
                },
            )
        extra_posts = [
            (
                "Chờ duyệt: kinh nghiệm người mới",
                "Mình mới xem cách chơi, chưa biết mua vé ở đâu.",
                "community",
                CommunityPost.STATUS_PENDING,
                "",
                0,
            ),
            (
                "Từ chối: bán số qua inbox",
                "Ib mình lấy số đẹp.",
                "community",
                CommunityPost.STATUS_REJECTED,
                "Spam / bán số / môi giới trái phép",
                0,
            ),
            (
                "Từ chối: cam kết trúng",
                "Kỳ này chắc trúng, soi cầu chuẩn.",
                "entertainment",
                CommunityPost.STATUS_REJECTED,
                "Spam / nội dung dự đoán chắc chắn",
                0,
            ),
        ]
        for i, (title, body, pillar, status, reason, comments) in enumerate(extra_posts):
            CommunityPost.objects.get_or_create(
                title=title,
                defaults={
                    "body": body,
                    "author_name": "Thành viên",
                    "pillar": pillar,
                    "status": status,
                    "comment_count": comments,
                    "rejection_reason": reason,
                    "created_at": now - timedelta(hours=2 + i),
                    "moderated_at": None if status == CommunityPost.STATUS_PENDING else now - timedelta(minutes=40),
                },
            )
        MinigameEvent.objects.get_or_create(
            title="Quiz kiến thức Keno (đã duyệt)",
            defaults={
                "description": "Câu hỏi về cách chơi và điểm bán. Không dự đoán số kỳ tới.",
                "scheduled_at": now + timedelta(days=2, hours=3),
                "reward_note": "Thẻ cà phê tượng trưng — không gắn kết quả xổ số.",
                "participants": 86,
            },
        )
        MinigameEvent.objects.get_or_create(
            title="Poll: tiện ích nào bạn dùng nhiều nhất?",
            defaults={
                "description": "Kết quả live, thống kê, dò vé hay tìm điểm bán — không gắn dự đoán số.",
                "scheduled_at": now - timedelta(days=4),
                "reward_note": "Không gắn kết quả xổ số.",
                "participants": 124,
            },
        )

    def _pos(self):
        group = pos_owner_group()
        owners = {}
        password = "keno-pos-2026"
        specs = (
            ("chudiem", "Điểm bán Keno Hoàn Kiếm", "chudiem@keno.local"),
            ("chudiem2", "Điểm bán Keno Quận 1", "chudiem2@keno.local"),
        )
        for username, _pos_name, email in specs:
            user, created = User.objects.get_or_create(username=username)
            user.email = email
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.set_password(password)
            user.save()
            user.groups.add(group)
            owners[username] = user
            action = "tạo" if created else "cập nhật"
            self.stdout.write(f"Chủ điểm bán {action}: {username} / {password}")
        for name, addr, dist, city, lat, lng, phone in POS:
            loc, _ = PosLocation.objects.get_or_create(
                name=name,
                defaults={
                    "address": addr,
                    "district": dist,
                    "city": city,
                    "latitude": lat,
                    "longitude": lng,
                    "phone": phone,
                },
            )
            fields = []
            if not (loc.address or "").strip():
                loc.address = addr
                fields.append("address")
            if not (loc.district or "").strip():
                loc.district = dist
                fields.append("district")
            if not (loc.city or "").strip():
                loc.city = city
                fields.append("city")
            if name == "Điểm bán Keno Hoàn Kiếm" and loc.owner_id != owners["chudiem"].id:
                loc.owner = owners["chudiem"]
                fields.append("owner")
            elif name == "Điểm bán Keno Quận 1" and loc.owner_id != owners["chudiem2"].id:
                loc.owner = owners["chudiem2"]
                fields.append("owner")
            if fields:
                loc.save(update_fields=fields)
        self.stdout.write("Chủ điểm bán: chudiem / keno-pos-2026 (Hoàn Kiếm); chudiem2 / keno-pos-2026 (Quận 1)")

    def _analytics(self):
        rng = random.Random(42)
        today = timezone.localdate()
        now = timezone.now()
        self._seed_google(rng, today)
        self._seed_events(rng, now)
        self._seed_community_kpis(rng, today)
        self._seed_technical(today)
        self._seed_o2o(rng, now)

    def _seed_google(self, rng, today):
        queries = [
            "kết quả keno",
            "kết quả keno hôm nay",
            "keno kỳ mới nhất",
            "thống kê keno",
            "cách chơi keno",
            "keno là gì",
            "điểm bán keno gần đây",
            "lịch sử keno",
            "cơ cấu giải thưởng keno",
            "keno vietlott",
        ]
        for i in range(60, 0, -1):
            day = today - timedelta(days=i)
            if GA4Snapshot.objects.filter(date=day).exists():
                continue
            growth = (60 - i) * 10
            base = 620 + growth + rng.randint(0, 50)
            organic = int(base * 0.58)
            GA4Snapshot.objects.create(
                date=day,
                active_users=base,
                new_users=int(base * 0.42),
                returning_users=int(base * 0.58),
                sessions=int(base * 1.35),
                organic_sessions=organic,
                referral_sessions=int(base * 0.12),
                engaged_sessions=int(base * 0.7),
                bounce_rate=round(38 + rng.random() * 8, 1),
                avg_session_duration=round(95 + rng.random() * 40, 1),
                pages_per_session=round(2.4 + rng.random(), 2),
                d7_retention=round(18 + rng.random() * 6, 1),
                d30_retention=round(8 + rng.random() * 4, 1),
            )
            clicks = 28 + i + rng.randint(0, 16)
            impressions = clicks * rng.randint(12, 18)
            GSCSnapshot.objects.update_or_create(
                date=day,
                defaults={
                    "clicks": clicks,
                    "impressions": impressions,
                    "ctr": round(100 * clicks / impressions, 2),
                    "position": round(8.5 + rng.random() * 6, 2),
                },
            )
            DailyMetric.objects.update_or_create(
                date=day,
                source=DailyMetric.SOURCE_GA4,
                metric_name="active_users",
                defaults={"value": base},
            )
            for q in queries:
                pos = round(3 + rng.random() * 12, 1)
                GSCQuery.objects.update_or_create(
                    date=day,
                    query=q,
                    defaults={
                        "clicks": rng.randint(2, 40),
                        "impressions": rng.randint(80, 900),
                        "ctr": round(rng.random() * 8, 2),
                        "position": pos,
                    },
                )

    def _seed_events(self, rng, now):
        if AnalyticsEvent.objects.count() >= 400:
            return
        weighted = (
            [AnalyticsEvent.RESULT_VIEW] * 28
            + [AnalyticsEvent.STATS_VIEW] * 16
            + [AnalyticsEvent.TICKET_CHECK] * 12
            + [AnalyticsEvent.SIMULATOR_PLAY] * 8
            + [AnalyticsEvent.FIND_POS_CLICK] * 10
            + [AnalyticsEvent.POS_SEARCH] * 7
            + [AnalyticsEvent.POS_DETAIL] * 6
            + [AnalyticsEvent.GET_DIRECTIONS] * 5
            + [AnalyticsEvent.LOCATION_PERMISSION] * 4
            + [AnalyticsEvent.COMMUNITY_CTA] * 6
            + [AnalyticsEvent.COMMUNITY_JOIN_INTENT] * 4
            + [AnalyticsEvent.VOUCHER_ISSUE] * 3
        )
        for _ in range(420):
            AnalyticsEvent.objects.create(
                event_name=rng.choice(weighted),
                session_key=f"demo-{rng.randint(1, 140)}",
                path="/",
                occurred_at=now - timedelta(hours=rng.randint(1, 24 * 28)),
            )

    def _seed_community_kpis(self, rng, today):
        if CommunityKpiSnapshot.objects.exists():
            return
        for i in range(30, 0, -1):
            day = today - timedelta(days=i)
            CommunityKpiSnapshot.objects.create(
                date=day,
                new_members=8 + rng.randint(0, 12),
                authentic_account_rate=round(91 + rng.random() * 6, 1),
                returning_active_pct=round(22 + rng.random() * 10, 1),
                notes="",
            )

    def _seed_technical(self, today):
        if TechnicalKpiSnapshot.objects.exists():
            return
        for i in range(14, 0, -1):
            day = today - timedelta(days=i)
            TechnicalKpiSnapshot.objects.create(
                date=day,
                mobile_perf_score=92,
                lcp_ms=2100,
                inp_ms=160,
                cls=0.08,
                realtime_latency_ms=1200,
                cwv_pass=True,
            )

    def _seed_o2o(self, rng, now):
        pos_by_name = {p.name: p for p in PosLocation.objects.all()}
        pos_names = [p[0] for p in POS]
        if not ExperienceCode.objects.exists():
            for i in range(28):
                created = now - timedelta(days=rng.randint(0, 25), hours=rng.randint(0, 20))
                pos = pos_by_name.get(rng.choice(pos_names))
                obj = ExperienceCode.objects.create(
                    code=f"K{1000 + i:04d}{rng.randint(10, 99)}",
                    expires_at=created + timedelta(hours=24),
                    session_key=f"demo-{rng.randint(1, 140)}",
                    pos=pos if rng.random() < 0.5 else None,
                    pos_name=pos.name if pos and rng.random() < 0.5 else "",
                )
                ExperienceCode.objects.filter(pk=obj.pk).update(created_at=created)
                if rng.random() < 0.38 and pos:
                    ExperienceCode.objects.filter(pk=obj.pk).update(
                        redeemed_at=created + timedelta(hours=rng.randint(1, 12)),
                        pos_id=pos.id,
                        pos_name=pos.name,
                    )
        for code in ExperienceCode.objects.filter(redeemed_at__isnull=False, pos__isnull=True):
            match = pos_by_name.get(code.pos_name)
            if match:
                code.pos = match
                code.save(update_fields=["pos"])
        from apps.locations.models import PayoutRequest

        credited = 0
        for code in ExperienceCode.objects.filter(redeemed_at__isnull=False, pos__isnull=False).select_related("pos"):
            if credit_o2o_commission(code):
                credited += 1
        owner = User.objects.filter(username="chudiem").first()
        if owner and not PayoutRequest.objects.filter(owner=owner).exists():
            from apps.locations.models import OwnerWallet

            wallet = OwnerWallet.objects.filter(user=owner).first()
            if wallet and wallet.points_balance >= 5:
                from apps.locations.services import request_payout

                try:
                    request_payout(owner, 5)
                except ValueError:
                    pass
        self.stdout.write(f"Hoa hồng O2O đã ghi nhận: {credited}")
