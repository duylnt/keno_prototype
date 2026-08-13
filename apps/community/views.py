from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.analytics.services import track
from apps.community.facebook import plugin_ready
from apps.core.models import Banner

from .models import (
    BannedKeyword,
    CommunityGuideline,
    CommunityPost,
    FacebookPagePost,
    JoinQuestion,
    MinigameEvent,
)


def _contains_banned(text: str) -> str | None:
    lowered = (text or "").lower()
    for kw in BannedKeyword.objects.filter(is_active=True):
        if kw.keyword.lower() in lowered:
            return kw.keyword
    return None


def hub(request):
    posts = CommunityPost.objects.filter(status=CommunityPost.STATUS_APPROVED)
    guidelines = CommunityGuideline.objects.filter(is_active=True)
    questions = JoinQuestion.objects.filter(is_active=True)
    events = MinigameEvent.objects.filter(is_published=True, scheduled_at__gte=timezone.now())[:5]
    banners = Banner.objects.filter(is_active=True, placement=Banner.PLACEMENT_COMMUNITY)
    fb_posts = FacebookPagePost.objects.filter(is_published=True, is_hidden=False)[:12]
    return render(
        request,
        "community/hub.html",
        {
            "posts": posts[:20],
            "guidelines": guidelines,
            "questions": questions,
            "events": events,
            "banners": banners,
            "fb_posts": fb_posts,
            "show_fb_page_plugin": plugin_ready(),
            "page_title": "Cộng đồng Keno",
            "meta_description": "Cộng đồng Keno trên Fanpage Facebook: bài viết, thảo luận và nội quy. Không phải kênh chính thức Vietlott.",
            "breadcrumbs": [("Trang chủ", "/"), ("Cộng đồng", "/cong-dong/")],
        },
    )


def submit_post(request):
    if request.method != "POST":
        return redirect("community:hub")
    title = (request.POST.get("title") or "").strip()[:200]
    body = (request.POST.get("body") or "").strip()
    author = (request.POST.get("author_name") or "Khách").strip()[:80]
    banned = _contains_banned(f"{title} {body} {author}")
    if banned:
        CommunityPost.objects.create(
            title=title or "(bị lọc)",
            body=body,
            author_name=author,
            status=CommunityPost.STATUS_REJECTED,
            rejection_reason=f"Từ khóa không phù hợp: {banned}",
        )
        messages.error(
            request,
            "Nội dung có dấu hiệu bán số, spam hoặc thông tin không phù hợp nên không được đăng.",
        )
        return redirect("community:hub")
    if not title or not body:
        messages.error(request, "Vui lòng nhập chủ đề và nội dung.")
        return redirect("community:hub")
    CommunityPost.objects.create(
        title=title,
        body=body,
        author_name=author,
        status=CommunityPost.STATUS_PENDING,
        pillar=CommunityPost.PILLAR_COMMUNITY,
    )
    messages.success(request, "Bài viết đã gửi và chờ kiểm duyệt.")
    return redirect("community:hub")


def guidelines(request):
    return render(
        request,
        "community/guidelines.html",
        {
            "guidelines": CommunityGuideline.objects.filter(is_active=True),
            "questions": JoinQuestion.objects.filter(is_active=True),
            "page_title": "Nội quy cộng đồng Keno",
            "meta_description": "Nội quy, câu hỏi lọc thành viên và nguyên tắc kiểm duyệt cộng đồng Keno.",
            "breadcrumbs": [
                ("Trang chủ", "/"),
                ("Thông tin", "/thong-tin/"),
                ("Nội quy", "/cong-dong/noi-quy/"),
            ],
        },
    )


def join_intent(request):
    track(request, "community_join_intent")
    from django.conf import settings

    from apps.core.context_processors import _clean_url
    from apps.core.models import SiteSettings

    site = SiteSettings.load()
    url = _clean_url(
        site.facebook_page_url,
        site.facebook_group_url,
        settings.FACEBOOK_PAGE_URL,
        settings.FACEBOOK_GROUP_URL,
    )
    if not url:
        return redirect("community:hub")
    return redirect(url)
