"""Unfold sidebar helpers for CMS reports."""

from django.http import HttpRequest

from apps.community.models import CommunityPost
from apps.locations.models import PayoutRequest


def pending_posts_badge(request: HttpRequest) -> int:
    return CommunityPost.objects.filter(status=CommunityPost.STATUS_PENDING).count()


def pending_payouts_badge(request: HttpRequest) -> int:
    return PayoutRequest.objects.filter(status=PayoutRequest.STATUS_PENDING).count()


def _path_is(request: HttpRequest, *names: str) -> bool:
    path = request.path.rstrip("/") + "/"
    return any(f"/cms/{name}/" in path or path.endswith(f"/{name}/") for name in names)


def active_home(request: HttpRequest) -> bool:
    return request.path.rstrip("/") in {"/cms", ""}


def active_funnel(request: HttpRequest) -> bool:
    return _path_is(request, "bao-cao/pheu", "bao-cao-kpi")


def active_website(request: HttpRequest) -> bool:
    return _path_is(request, "bao-cao/website")


def active_seo(request: HttpRequest) -> bool:
    return _path_is(request, "bao-cao/seo")


def active_community_report(request: HttpRequest) -> bool:
    return _path_is(request, "bao-cao/cong-dong")


def active_o2o(request: HttpRequest) -> bool:
    return _path_is(request, "bao-cao/o2o")
