from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.core.models import SiteSettings

from .auth import is_pos_owner, owned_locations
from .models import (
    CommissionLedger,
    ExperienceCode,
    OwnerWallet,
    PayoutRequest,
    WalletTransaction,
)
from .services import request_payout, vnd_per_point


def pos_owner_required(view):
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("locations:partner_login")
        if request.user.is_staff and not is_pos_owner(request.user):
            messages.info(request, "Tài khoản CMS dùng /cms/, không dùng cổng điểm bán.")
            return redirect("/cms/")
        if not is_pos_owner(request.user):
            logout(request)
            messages.error(request, "Tài khoản này chưa được gán điểm bán.")
            return redirect("locations:partner_login")
        return view(request, *args, **kwargs)

    return _wrapped


def partner_login(request):
    if request.user.is_authenticated and is_pos_owner(request.user):
        return redirect("locations:partner_dashboard")
    error = ""
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = _login_failure_message(username, password)
        elif is_pos_owner(user):
            login(request, user)
            return redirect("locations:partner_dashboard")
        elif user.is_staff:
            login(request, user)
            messages.info(request, "Tài khoản nhân viên — chuyển tới CMS.")
            return redirect("/cms/")
        else:
            error = "Tài khoản chưa được gán làm chủ điểm bán (nhóm pos_owner hoặc owner trên Điểm bán)."
    return render(
        request,
        "partners/login.html",
        {
            "error": error,
            "page_title": "Đăng nhập điểm bán",
            "seo_robots": "noindex,nofollow",
        },
    )


def _login_failure_message(username: str, password: str) -> str:
    User = get_user_model()
    if not username or not password:
        return "Nhập tên đăng nhập và mật khẩu."
    existing = User.objects.filter(username=username).first()
    if existing is None:
        return "Không tìm thấy tài khoản."
    if not existing.is_active:
        return "Tài khoản đã bị khóa."
    if not existing.has_usable_password():
        return "Tài khoản chưa có mật khẩu."
    if not existing.check_password(password):
        return "Sai mật khẩu."
    return "Không đăng nhập được. Thử lại."


def partner_logout(request):
    logout(request)
    return redirect("locations:partner_login")


def _dashboard_context(request):
    site = SiteSettings.load()
    locations = list(owned_locations(request.user))
    loc_ids = [loc.pk for loc in locations]
    days_raw = request.GET.get("days") or "30"
    try:
        days = int(days_raw)
    except (TypeError, ValueError):
        days = 30
    if days not in (7, 30, 90):
        days = 30
    now = timezone.localtime()
    since = now - timedelta(days=days)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ledgers = CommissionLedger.objects.filter(pos_id__in=loc_ids)
    redeems = ExperienceCode.objects.filter(
        pos_id__in=loc_ids, redeemed_at__isnull=False
    ).select_related("pos")
    month_vnd = (
        ledgers.filter(created_at__gte=month_start).aggregate(s=Sum("amount_vnd"))["s"] or 0
    )
    week_vnd = (
        ledgers.filter(created_at__gte=now - timedelta(days=7)).aggregate(s=Sum("amount_vnd"))["s"]
        or 0
    )
    total_vnd = ledgers.aggregate(s=Sum("amount_vnd"))["s"] or 0
    month_redeems = redeems.filter(redeemed_at__gte=month_start).count()
    wallet, _ = OwnerWallet.objects.get_or_create(user=request.user)
    rate = vnd_per_point(site)
    table = (
        redeems.filter(redeemed_at__gte=since)
        .select_related("pos", "commission")
        .order_by("-redeemed_at")[:80]
    )
    return {
        "page_title": "Cổng đối tác — điểm bán",
        "seo_robots": "noindex,nofollow",
        "locations": locations,
        "primary_pos": locations[0] if locations else None,
        "days": days,
        "month_vnd": month_vnd,
        "week_vnd": week_vnd,
        "total_vnd": total_vnd,
        "month_redeems": month_redeems,
        "wallet": wallet,
        "wallet_vnd": wallet.vnd_equivalent(rate),
        "vnd_per_point": rate,
        "redeems": table,
        "ledger_count": ledgers.aggregate(n=Count("id"))["n"] or 0,
        "transactions": WalletTransaction.objects.filter(wallet=wallet)[:12],
        "payouts": PayoutRequest.objects.filter(owner=request.user)[:8],
        "site_settings": site,
    }


@pos_owner_required
def partner_dashboard(request):
    return render(request, "partners/dashboard.html", _dashboard_context(request))


@pos_owner_required
def partner_payout(request):
    if request.method != "POST":
        return redirect("locations:partner_dashboard")
    raw = (request.POST.get("points") or "").strip()
    try:
        points = int(raw)
    except (TypeError, ValueError):
        messages.error(request, "Số điểm không hợp lệ.")
        return redirect("locations:partner_dashboard")
    try:
        request_payout(request.user, points)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Đã gửi yêu cầu quy đổi.")
    return redirect("locations:partner_dashboard")
