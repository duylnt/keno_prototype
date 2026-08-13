import json
import math
import secrets
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.analytics.services import track
from apps.core.models import Banner

from .models import ExperienceCode, PosLocation
from .services import credit_o2o_commission


def _haversine(lat1, lon1, lat2, lon2):
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def finder(request):
    track(request, "find_pos_click", path=request.path)
    locations = PosLocation.objects.filter(is_active=True)
    banners = Banner.objects.filter(is_active=True, placement=Banner.PLACEMENT_POS)
    cities = locations.values_list("city", flat=True).distinct().order_by("city")
    payload = [
        {
            "id": loc.id,
            "name": loc.name,
            "address": loc.address,
            "district": loc.district,
            "city": loc.city,
            "lat": float(loc.latitude),
            "lng": float(loc.longitude),
            "phone": loc.phone,
            "hours": loc.opening_hours,
            "url": loc.get_absolute_url(),
            "directions": loc.maps_directions_url,
        }
        for loc in locations
    ]
    return render(
        request,
        "locations/finder.html",
        {
            "locations": locations,
            "locations_json": json.dumps(payload, ensure_ascii=False),
            "cities": cities,
            "banners": banners,
            "auto_gps": request.GET.get("gps") in {"1", "true", "yes"},
            "page_title": "Tìm điểm bán Keno gần bạn",
            "meta_description": "Xác định điểm bán Keno gần vị trí của bạn và chỉ đường đến điểm bán. Không bán vé trên website.",
            "breadcrumbs": [("Trang chủ", "/"), ("Điểm bán", "/diem-ban/")],
        },
    )


def pos_detail(request, pk):
    loc = get_object_or_404(PosLocation, pk=pk, is_active=True)
    track(request, "pos_detail", metadata={"pos_id": loc.id})
    nearby = PosLocation.objects.filter(is_active=True, city=loc.city).exclude(pk=loc.pk)[:5]
    return render(
        request,
        "locations/detail.html",
        {
            "loc": loc,
            "nearby": nearby,
            "page_title": f"{loc.name} — Điểm bán Keno",
            "meta_description": loc.address,
            "breadcrumbs": [("Trang chủ", "/"), ("Điểm bán", "/diem-ban/"), (loc.name, loc.get_absolute_url())],
        },
    )


@require_POST
def nearby_api(request):
    try:
        data = json.loads(request.body.decode() or "{}")
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid"}, status=400)
    track(request, "location_permission")
    track(request, "pos_search", metadata={"lat": lat, "lng": lng})
    rows = []
    for loc in PosLocation.objects.filter(is_active=True):
        dist = _haversine(lat, lng, float(loc.latitude), float(loc.longitude))
        rows.append(
            {
                "id": loc.id,
                "name": loc.name,
                "address": loc.address,
                "city": loc.city,
                "lat": float(loc.latitude),
                "lng": float(loc.longitude),
                "km": round(dist, 2),
                "url": loc.get_absolute_url(),
                "directions": loc.maps_directions_url,
                "hours": loc.opening_hours,
            }
        )
    rows.sort(key=lambda x: x["km"])
    return JsonResponse({"results": rows[:12]})


def voucher(request):
    code = None
    if request.method == "POST":
        code = ExperienceCode.objects.create(
            code=secrets.token_hex(4).upper(),
            expires_at=timezone.now() + timedelta(hours=24),
            session_key=request.session.session_key or "",
        )
        track(request, "voucher_issue", metadata={"code": code.code})
    return render(
        request,
        "locations/voucher.html",
        {
            "code": code,
            "page_title": "Mã trải nghiệm O2O",
            "meta_description": "Nhận mã trải nghiệm để xuất trình tại điểm bán Keno.",
            "breadcrumbs": [("Trang chủ", "/"), ("Mã trải nghiệm", "/ma-trai-nghiem/")],
        },
    )


def redeem(request):
    message = ""
    found = None
    if request.method == "POST":
        raw = (request.POST.get("code") or "").strip().upper()
        pos_id = request.POST.get("pos_id")
        pos = PosLocation.objects.filter(pk=pos_id, is_active=True).first()
        found = ExperienceCode.objects.filter(code=raw).first()
        if not found:
            message = "Không tìm thấy mã."
        elif found.is_redeemed:
            message = "Mã đã được quét trước đó."
        elif found.is_expired:
            message = "Mã đã hết hạn."
        elif not pos:
            message = "Chọn điểm bán để ghi nhận hoa hồng."
        else:
            found.redeemed_at = timezone.now()
            found.pos = pos
            found.pos_name = pos.name
            found.save(update_fields=["redeemed_at", "pos", "pos_name"])
            credit_o2o_commission(found)
            message = "Quét thành công — ghi nhận chuyển đổi digital → POS."
    return render(
        request,
        "locations/redeem.html",
        {
            "message": message,
            "found": found,
            "locations": PosLocation.objects.filter(is_active=True),
            "page_title": "Quét mã O2O tại POS",
            "seo_robots": "noindex,follow",
        },
    )
