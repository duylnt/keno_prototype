import json

from django.http import JsonResponse
from django.shortcuts import render

from apps.community.models import CommunityPost
from apps.content.models import Article
from apps.core.live_pip import arm_watching
from apps.locations.models import PosLocation
from apps.results.services import countdown_seconds, homepage_stats, latest_draw, next_draw_at, pos_tv_payload


def home(request):
    draw = latest_draw()
    stats = homepage_stats(50)
    articles = Article.objects.filter(is_published=True, robots_noindex=False).select_related("category")[:4]
    cities = (
        PosLocation.objects.filter(is_active=True)
        .values_list("city", flat=True)
        .distinct()
        .order_by("city")
    )
    return render(
        request,
        "core/home.html",
        {
            "draw": draw,
            "countdown": countdown_seconds(),
            "next_draw": next_draw_at(),
            "articles": articles,
            "cities": cities,
            "stats": stats,
            "home_stats_json": json.dumps(stats["charts"]),
            "page_title": "Keno — Kết quả, thống kê & điểm bán gần bạn",
            "meta_description": (
                "Tra cứu kết quả Keno theo từng kỳ 8 phút, xem thống kê Lớn/Nhỏ Chẵn/Lẻ, "
                "dò vé, chơi thử và tìm điểm bán Keno gần bạn."
            ),
            "breadcrumbs": [("Trang chủ", "/")],
        },
    )


def pos_display(request):
    payload = pos_tv_payload()
    discussion_posts = CommunityPost.objects.filter(status=CommunityPost.STATUS_APPROVED)[:6]
    response = render(
        request,
        "core/pos_display.html",
        {
            "pos": payload,
            "discussion_posts": discussion_posts,
            "page_title": "Trực tiếp kết quả Keno",
            "meta_description": (
                "Xem trực tiếp mô phỏng quay số Keno, thảo luận cộng đồng "
                "và tìm điểm bán gần bạn — website không bán vé."
            ),
            "seo_robots": "noindex,follow",
            "ball_slots": range(20),
            "grid_numbers": range(1, 81),
        },
    )
    return arm_watching(response)


def pos_tv_api(request):
    return JsonResponse(pos_tv_payload(), json_dumps_params={"ensure_ascii": False})
