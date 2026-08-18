from django.conf import settings
from django.urls import reverse

from apps.community.models import CommunityPost
from apps.core.live_pip import pip_flags
from apps.core.models import Banner, SiteSettings
from apps.core.nav import nav_on
from apps.results.services import countdown_seconds, latest_draw, next_draw_at, pos_tv_payload

_FB_PLACEHOLDERS = {
    "",
    "https://www.facebook.com/groups/",
    "https://www.facebook.com/groups",
    "https://facebook.com/groups/",
    "https://facebook.com/groups",
}


def _clean_url(*candidates):
    for raw in candidates:
        value = (raw or "").strip()
        if value and value.rstrip("/") not in {p.rstrip("/") for p in _FB_PLACEHOLDERS}:
            return value
    return ""


def site_chrome(request):
    site = SiteSettings.load()
    # Never expose the Page token to templates (public or CMS chrome).
    site.facebook_page_access_token = ""
    featured = CommunityPost.objects.filter(
        status=CommunityPost.STATUS_APPROVED, is_featured=True
    )[:4]
    facebook_group_url = _clean_url(site.facebook_group_url, settings.FACEBOOK_GROUP_URL)
    facebook_page_url = _clean_url(site.facebook_page_url, settings.FACEBOOK_PAGE_URL)
    facebook_app_id = (site.facebook_app_id or settings.FACEBOOK_APP_ID or "").strip()
    facebook_comments_url = _clean_url(
        site.facebook_comments_url,
        settings.FACEBOOK_COMMENTS_URL,
        facebook_page_url,
        f"{settings.SITE_URL}{reverse('core:live_results')}",
    )
    zalo_group_url = _clean_url(site.zalo_group_url, settings.ZALO_GROUP_URL)
    facebook_open_url = facebook_page_url or facebook_group_url
    flags = nav_on(request)
    latest = latest_draw()
    live_pip = pip_flags(
        request,
        on_live=flags["live"],
        period=latest.period_code if latest else "",
    )
    ctx = {
        "site_settings": site,
        "ga4_id": site.ga4_measurement_id or settings.GA4_MEASUREMENT_ID,
        "gtm_id": site.gtm_container_id or settings.GTM_CONTAINER_ID,
        "featured_posts": featured,
        "home_banners": Banner.objects.filter(is_active=True, placement=Banner.PLACEMENT_HOME)[:3],
        "nav_countdown": countdown_seconds(),
        "nav_next_draw": next_draw_at(),
        "nav_latest": latest,
        "facebook_group_url": facebook_group_url,
        "facebook_page_url": facebook_page_url,
        "facebook_app_id": facebook_app_id,
        "facebook_comments_url": facebook_comments_url,
        "facebook_open_url": facebook_open_url,
        "zalo_group_url": zalo_group_url,
        "buy_ticket_gps_url": reverse("locations:finder") + "?gps=1",
        "load_fb_sdk": bool(facebook_app_id or facebook_page_url),
        "nav_on": flags,
        "live_pip": live_pip,
    }
    if live_pip["visible"]:
        ctx["pos"] = pos_tv_payload()
        ctx["ball_slots"] = range(20)
        ctx["grid_numbers"] = range(1, 81)
    return ctx
