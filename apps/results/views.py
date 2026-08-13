import json
from datetime import timedelta

from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.analytics.services import track

from .models import Draw
from .services import (
    check_ticket,
    countdown_seconds,
    ensure_draws_up_to_now,
    frequency_stats,
    latest_draw,
    next_draw_at,
    size_parity_series,
)


def _draw_payload(draw: Draw | None) -> dict:
    if not draw:
        return {}
    return {
        "period_code": draw.period_code,
        "drawn_at": timezone.localtime(draw.drawn_at).strftime("%H:%M %d/%m/%Y"),
        "numbers": draw.numbers_sorted,
        "total": draw.total,
        "size": draw.size,
        "size_label": draw.size_label,
        "parity": draw.parity,
        "parity_label": draw.parity_label,
        "even_count": draw.even_count,
        "odd_count": draw.odd_count,
        "is_simulated": draw.is_simulated,
        "countdown": countdown_seconds(),
        "next_draw": timezone.localtime(next_draw_at()).strftime("%H:%M") if next_draw_at() else "",
    }


def live(request):
    draw = latest_draw()
    track(request, "result_view", path=request.path)
    return render(
        request,
        "results/live.html",
        {
            "draw": draw,
            "countdown": countdown_seconds(),
            "next_draw": next_draw_at(),
            "recent": Draw.objects.all()[:8],
            "page_title": "Kết quả Keno mới nhất",
            "meta_description": "Xem kết quả Keno kỳ mới nhất và đếm ngược kỳ quay 8 phút tiếp theo.",
            "breadcrumbs": [("Trang chủ", "/"), ("Kết quả", "/ket-qua/")],
        },
    )


def today(request):
    ensure_draws_up_to_now()
    day = timezone.localdate()
    draws = Draw.objects.filter(draw_date=day)
    track(request, "result_view", path=request.path)
    return render(
        request,
        "results/today.html",
        {
            "draws": draws,
            "day": day,
            "page_title": "Kết quả Keno hôm nay",
            "meta_description": "Lịch sử kết quả Keno theo từng kỳ quay trong ngày. Prototype cộng đồng, không thay thế kết quả tại điểm bán.",
            "breadcrumbs": [("Trang chủ", "/"), ("Kết quả", "/ket-qua/"), ("Hôm nay", "/ket-qua/hom-nay/")],
        },
    )


def history(request):
    ensure_draws_up_to_now()
    draws = Draw.objects.all()
    selected = request.GET.get("date")
    if selected:
        draws = draws.filter(draw_date=selected)
    else:
        draws = draws[:80]
    track(request, "result_view", path=request.path)
    return render(
        request,
        "results/history.html",
        {
            "draws": draws,
            "selected": selected,
            "page_title": "Lịch sử kết quả Keno",
            "meta_description": "Xem lịch sử kết quả các kỳ quay Keno theo ngày.",
            "breadcrumbs": [("Trang chủ", "/"), ("Kết quả", "/ket-qua/"), ("Lịch sử", "/ket-qua/lich-su/")],
        },
    )


def stats(request):
    ensure_draws_up_to_now()
    limit = int(request.GET.get("n", 50))
    limit = max(10, min(limit, 200))
    draws = list(Draw.objects.all()[:limit])
    freq = frequency_stats(draws)
    series = size_parity_series(draws)
    hot = sorted(freq, key=lambda x: x["count"], reverse=True)[:10]
    cold = sorted(freq, key=lambda x: x["count"])[:10]
    track(request, "stats_view", path=request.path)
    return render(
        request,
        "results/stats.html",
        {
            "limit": limit,
            "freq": freq,
            "series": series,
            "series_json": json.dumps(series),
            "freq_json": json.dumps(freq),
            "hot": hot,
            "cold": cold,
            "page_title": "Thống kê Keno",
            "meta_description": "Thống kê tần suất, Lớn/Nhỏ, Chẵn/Lẻ các kỳ quay Keno.",
            "disclaimer": True,
            "breadcrumbs": [("Trang chủ", "/"), ("Thống kê", "/thong-ke/")],
            "faq_items": [
                {"q": "Thống kê Keno có giúp trúng không?", "a": "Không. Thống kê mô tả dữ liệu quá khứ, không dự đoán kỳ tới và không làm tăng khả năng trúng."},
                {"q": "Lớn/Nhỏ tính thế nào?", "a": "Dựa trên tổng 20 số quay: Nhỏ 210–810, Lớn 811–1410 (theo mô tả sản phẩm)."},
            ],
        },
    )


def stats_size(request):
    ensure_draws_up_to_now()
    draws = list(Draw.objects.all()[:100])
    series = size_parity_series(draws)
    track(request, "stats_view", path=request.path)
    return render(
        request,
        "results/stats_size.html",
        {
            "draws": draws[:40],
            "series": series,
            "series_json": json.dumps(series),
            "page_title": "Lịch sử Lớn / Nhỏ Keno",
            "meta_description": "Theo dõi lịch sử Lớn/Nhỏ các kỳ quay Keno. Tham khảo, không dự đoán.",
            "breadcrumbs": [("Trang chủ", "/"), ("Thống kê", "/thong-ke/"), ("Lớn/Nhỏ", "/thong-ke/lon-nho/")],
        },
    )


def stats_parity(request):
    ensure_draws_up_to_now()
    draws = list(Draw.objects.all()[:100])
    series = size_parity_series(draws)
    track(request, "stats_view", path=request.path)
    return render(
        request,
        "results/stats_parity.html",
        {
            "draws": draws[:40],
            "series": series,
            "series_json": json.dumps(series),
            "page_title": "Lịch sử Chẵn / Lẻ Keno",
            "meta_description": "Theo dõi lịch sử Chẵn/Lẻ các kỳ quay Keno. Tham khảo, không dự đoán.",
            "breadcrumbs": [("Trang chủ", "/"), ("Thống kê", "/thong-ke/"), ("Chẵn/Lẻ", "/thong-ke/chan-le/")],
        },
    )


def check_ticket_view(request):
    ensure_draws_up_to_now()
    result = None
    error = ""
    latest = latest_draw()
    if request.method == "POST":
        period = (request.POST.get("period_code") or "").strip()
        raw = request.POST.get("numbers") or ""
        try:
            picked = sorted({int(x) for x in raw.replace(",", " ").split() if x.strip()})
        except ValueError:
            picked = []
        if not picked or any(n < 1 or n > 80 for n in picked) or len(picked) > 10:
            error = "Nhập 1–10 số nguyên từ 01 đến 80, không trùng."
        else:
            draw = Draw.objects.filter(period_code=period).first() or latest
            if not draw:
                error = "Chưa có kỳ quay để dò."
            else:
                result = check_ticket(picked, draw)
                track(request, "ticket_check", metadata={"matches": result["match_count"]})
    return render(
        request,
        "results/check_ticket.html",
        {
            "latest": latest,
            "recent": Draw.objects.all()[:20],
            "result": result,
            "error": error,
            "page_title": "Dò vé Keno",
            "meta_description": "Nhập dãy số để kiểm tra kết quả kỳ quay Keno. Không thay thế xác nhận tại điểm bán.",
            "breadcrumbs": [("Trang chủ", "/"), ("Dò vé", "/do-ve/")],
        },
    )


def simulator(request):
    return render(
        request,
        "results/simulator.html",
        {
            "page_title": "Chơi thử Keno",
            "meta_description": "Chơi thử Keno: chọn số rồi quay một kỳ mô phỏng.",
            "breadcrumbs": [
                ("Trang chủ", "/"),
                ("Thông tin", "/thong-tin/"),
                ("Chơi thử", "/choi-thu/"),
            ],
        },
    )


@require_POST
def simulator_play(request):
    raw = request.POST.get("numbers") or request.body
    if isinstance(raw, bytes):
        try:
            payload = json.loads(raw.decode() or "{}")
            picked = [int(n) for n in payload.get("numbers", [])]
        except (json.JSONDecodeError, ValueError):
            picked = []
    else:
        try:
            picked = sorted({int(x) for x in raw.replace(",", " ").split() if x.strip()})
        except ValueError:
            picked = []
    picked = [n for n in picked if 1 <= n <= 80][:10]
    from .services import attributes_for, generate_numbers

    drawn = generate_numbers()
    attrs = attributes_for(drawn)
    matched = sorted(set(picked) & set(drawn))
    track(request, "simulator_play", metadata={"picks": len(picked), "matches": len(matched)})
    return JsonResponse(
        {
            "drawn": drawn,
            "picked": picked,
            "matched": matched,
            "match_count": len(matched),
            **attrs,
            "size_label": "Lớn" if attrs["size"] == "big" else "Nhỏ",
            "parity_label": {"even": "Chẵn", "odd": "Lẻ", "draw": "Hòa"}.get(attrs["parity"]),
        }
    )


@require_GET
def live_api(request):
    draw = latest_draw()
    return JsonResponse(_draw_payload(draw))


def live_sse(request):
    def stream():
        last = None
        while True:
            draw = latest_draw()
            payload = _draw_payload(draw)
            stamp = payload.get("period_code")
            if stamp != last:
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                last = stamp
            else:
                yield f"data: {json.dumps({'countdown': countdown_seconds(), 'heartbeat': True})}\n\n"
            import time

            time.sleep(2)

    response = StreamingHttpResponse(stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
