from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.seo.utils import absolute_url

from .models import Article, ArticleCategory, StaticPage

INFO_CRUMB = ("Thông tin", "/thong-tin/")

HOWTO_STEPS = [
    {
        "name": "Chọn số",
        "text": "Chọn từ 1 đến 10 số trong dải 01–80, hoặc chọn cửa Lớn/Nhỏ, Chẵn/Lẻ theo quy định tại điểm bán.",
    },
    {
        "name": "Mua vé tại điểm bán",
        "text": "Keno chỉ được phân phối tại các điểm bán chính thức. Website này không bán vé trực tuyến.",
    },
    {
        "name": "Chờ kỳ quay 8 phút",
        "text": "Mỗi kỳ mở thưởng 20 số, khung giờ 06:00–21:52.",
    },
    {
        "name": "Đối chiếu kết quả",
        "text": "Dùng trang Dò vé hoặc kiểm tra tại điểm bán. Xác nhận cuối cùng thuộc về điểm bán.",
    },
]

HOWTO_FAQS = [
    {
        "q": "Keno là gì?",
        "a": "Keno là sản phẩm xổ số nhanh: mỗi kỳ quay 20 số từ 01 đến 80; người chơi chọn 1–10 số. Mở thưởng mỗi 8 phút trong khung 06:00–21:52.",
    },
    {
        "q": "Mua vé Keno online được không?",
        "a": "Không trên website này. Vé chỉ bán tại điểm bán chính thức. Trang này hỗ trợ tra cứu, hướng dẫn và tìm điểm bán.",
    },
    {
        "q": "Thống kê có giúp trúng Keno không?",
        "a": "Không. Thống kê chỉ mô tả dữ liệu quá khứ, không phải công cụ dự đoán và không làm tăng khả năng trúng.",
    },
]


def info_hub(request):
    articles = Article.objects.filter(is_published=True, robots_noindex=False).select_related("category")[:8]
    return render(
        request,
        "content/info_hub.html",
        {
            "articles": articles,
            "page_title": "Thông tin Keno",
            "meta_description": "Cách chơi, chơi thử, chơi có trách nhiệm, nội quy cộng đồng và bài viết Keno.",
            "breadcrumbs": [("Trang chủ", "/"), INFO_CRUMB],
            "hub_cards": [
                {
                    "title": "Cách chơi",
                    "desc": "Hướng dẫn chọn số, mua vé tại điểm bán và đối chiếu kết quả.",
                    "href": reverse("content:how_to_play"),
                    "kicker": "Người mới",
                },
                {
                    "title": "Chơi thử",
                    "desc": "Mô phỏng một kỳ quay. Không dùng tiền thật, không phải mua vé.",
                    "href": reverse("results:simulator"),
                    "kicker": "Mô phỏng",
                },
                {
                    "title": "Chơi có trách nhiệm",
                    "desc": "Keno là giải trí. Không chơi quá khả năng tài chính, không tin cam kết trúng.",
                    "href": reverse("content:static_page", args=["choi-co-trach-nhiem"]),
                    "kicker": "An toàn",
                },
                {
                    "title": "Nội quy cộng đồng",
                    "desc": "Quy tắc thảo luận, kiểm duyệt và câu hỏi lọc thành viên.",
                    "href": reverse("community:guidelines"),
                    "kicker": "Cộng đồng",
                },
            ],
        },
    )


def article_list(request):
    articles = Article.objects.filter(is_published=True, robots_noindex=False).select_related("category")
    slug = request.GET.get("nhom")
    category = None
    if slug:
        category = get_object_or_404(ArticleCategory, slug=slug)
        articles = articles.filter(category=category)
    return render(
        request,
        "content/article_list.html",
        {
            "articles": articles,
            "categories": ArticleCategory.objects.all(),
            "category": category,
            "page_title": "Tin & hướng dẫn Keno",
            "meta_description": "Bài viết về kết quả, cách chơi, thống kê và cộng đồng Keno.",
            "breadcrumbs": [("Trang chủ", "/"), INFO_CRUMB, ("Bài viết", "/bai-viet/")],
        },
    )


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    related = (
        Article.objects.filter(is_published=True, category=article.category, robots_noindex=False)
        .exclude(pk=article.pk)[:3]
    )
    faqs = list(article.faqs.all())
    robots = "noindex,follow" if article.robots_noindex else "index,follow"
    canonical = article.canonical_url or article.get_absolute_url()
    return render(
        request,
        "content/article_detail.html",
        {
            "article": article,
            "article_faqs": faqs,
            "related": related,
            "page_title": article.meta_title,
            "meta_description": article.meta_description,
            "canonical_url": absolute_url(canonical),
            "seo_og_type": "article",
            "seo_og_image": article.og_image_url,
            "seo_robots": robots,
            "breadcrumbs": [
                ("Trang chủ", "/"),
                INFO_CRUMB,
                ("Bài viết", "/bai-viet/"),
                (article.title, article.get_absolute_url()),
            ],
        },
    )


def static_page(request, slug):
    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    robots = "noindex,follow" if page.robots_noindex else "index,follow"
    canonical = page.canonical_url or page.get_absolute_url()
    return render(
        request,
        "content/static_page.html",
        {
            "page": page,
            "page_title": page.meta_title,
            "meta_description": page.meta_description,
            "canonical_url": absolute_url(canonical),
            "seo_robots": robots,
            "seo_og_image": absolute_url(page.og_image.url) if page.og_image else "",
            "breadcrumbs": (
                [("Trang chủ", "/"), INFO_CRUMB, (page.title, page.get_absolute_url())]
                if slug == "choi-co-trach-nhiem"
                else [("Trang chủ", "/"), (page.title, page.get_absolute_url())]
            ),
        },
    )


def how_to_play(request):
    page = StaticPage.objects.filter(slug="cach-choi-keno", is_published=True).first()
    article = Article.objects.filter(slug="cach-choi-keno", is_published=True).first()
    faqs = list(article.faqs.all()) if article else []
    faq_items = [{"q": f.question, "a": f.answer} for f in faqs] or HOWTO_FAQS
    return render(
        request,
        "content/how_to_play.html",
        {
            "page": page,
            "article": article,
            "howto_steps": HOWTO_STEPS,
            "howto_name": "Cách chơi Keno",
            "faq_items": faq_items,
            "page_title": "Cách chơi Keno",
            "meta_description": "Hướng dẫn Keno cho người mới: chọn số, Lớn/Nhỏ Chẵn/Lẻ, mua vé tại điểm bán và cách kiểm tra kết quả. Không phải kênh chính thức Vietlott.",
            "breadcrumbs": [("Trang chủ", "/"), INFO_CRUMB, ("Cách chơi", "/huong-dan/")],
        },
    )
