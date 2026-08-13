"""Keno draw schedule and simulated result generation.

Vietlott Keno public rules used for labels (educational):
- 20 numbers drawn from 1–80
- Draws every 8 minutes from 06:00 to 21:52 (Asia/Ho_Chi_Minh)
- Big: sum 811–1410 · Small: sum 210–810
- Even/Odd by count of even numbers among the 20: ≥11 even, ≥11 odd, or 10-10 Hòa

Prototype results are simulated and must never be presented as official Vietlott results.
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from .models import Draw

DRAW_START = time(6, 0)
DRAW_END = time(21, 52)
INTERVAL = timedelta(minutes=8)
POOL = list(range(1, 81))


def _tz():
    return timezone.get_current_timezone()


def iter_draw_slots(day: date):
    tz = _tz()
    start = timezone.make_aware(datetime.combine(day, DRAW_START), tz)
    end = timezone.make_aware(datetime.combine(day, DRAW_END), tz)
    current = start
    seq = 1
    while current <= end:
        yield seq, current
        current += INTERVAL
        seq += 1


def period_code(day: date, sequence: int) -> str:
    return f"{day:%Y%m%d}-{sequence:03d}"


def attributes_for(numbers: list[int]) -> dict:
    total = sum(numbers)
    even_count = sum(1 for n in numbers if n % 2 == 0)
    odd_count = 20 - even_count
    size = Draw.SIZE_BIG if total >= 811 else Draw.SIZE_SMALL
    if even_count > odd_count:
        parity = Draw.PARITY_EVEN
    elif odd_count > even_count:
        parity = Draw.PARITY_ODD
    else:
        parity = Draw.PARITY_DRAW
    return {
        "total": total,
        "size": size,
        "even_count": even_count,
        "odd_count": odd_count,
        "parity": parity,
    }


def next_draw_at(now=None):
    now = now or timezone.localtime()
    day = now.date()
    for _seq, slot in iter_draw_slots(day):
        if slot > now:
            return slot
    tomorrow = day + timedelta(days=1)
    for _seq, slot in iter_draw_slots(tomorrow):
        return slot
    return None


def current_or_last_slot(now=None):
    now = now or timezone.localtime()
    last = None
    for seq, slot in iter_draw_slots(now.date()):
        if slot <= now:
            last = (seq, slot)
        else:
            break
    if last:
        return last
    yesterday = now.date() - timedelta(days=1)
    slots = list(iter_draw_slots(yesterday))
    return slots[-1] if slots else None


def generate_numbers(rng: random.Random | None = None) -> list[int]:
    rng = rng or random.Random()
    return sorted(rng.sample(POOL, 20))


def create_draw(day: date, sequence: int, drawn_at, rng: random.Random | None = None) -> Draw:
    numbers = generate_numbers(rng)
    attrs = attributes_for(numbers)
    return Draw.objects.create(
        period_code=period_code(day, sequence),
        draw_date=day,
        sequence=sequence,
        drawn_at=drawn_at,
        numbers=numbers,
        is_simulated=True,
        **attrs,
    )


def ensure_draws_up_to_now(now=None, lookback_days: int = 0) -> int:
    """Create missing simulated draws for completed slots up to `now`."""
    now = now or timezone.localtime()
    created = 0
    start_day = now.date() - timedelta(days=lookback_days)
    day = start_day
    while day <= now.date():
        for seq, slot in iter_draw_slots(day):
            if slot > now:
                break
            code = period_code(day, seq)
            if not Draw.objects.filter(period_code=code).exists():
                seed = int(slot.timestamp())
                create_draw(day, seq, slot, rng=random.Random(seed))
                created += 1
        day += timedelta(days=1)
    return created


def latest_draw() -> Draw | None:
    ensure_draws_up_to_now()
    return Draw.objects.order_by("-drawn_at").first()


def countdown_seconds(now=None) -> int:
    nxt = next_draw_at(now)
    now = now or timezone.localtime()
    if not nxt:
        return 0
    return max(0, int((nxt - now).total_seconds()))


def check_ticket(picked: list[int], draw: Draw) -> dict:
    drawn = set(draw.numbers or [])
    matched = sorted(n for n in picked if n in drawn)
    return {
        "picked": picked,
        "matched": matched,
        "match_count": len(matched),
        "draw": draw,
    }


def frequency_stats(draws) -> list[dict]:
    counts = {n: 0 for n in POOL}
    total_draws = 0
    for draw in draws:
        total_draws += 1
        for n in draw.numbers or []:
            counts[n] += 1
    return [
        {
            "number": n,
            "count": counts[n],
            "pct": round((counts[n] / total_draws) * 100, 1) if total_draws else 0,
        }
        for n in POOL
    ]


def homepage_stats(sample: int = 50) -> dict:
    """Compact dashboard stats for the public homepage, from simulated draws."""
    ensure_draws_up_to_now()
    today = timezone.localdate()
    now = timezone.localtime()
    week_start = today - timedelta(days=6)

    today_count = Draw.objects.filter(draw_date=today).count()
    week_count = Draw.objects.filter(draw_date__gte=week_start).count()
    scheduled_today = sum(1 for _ in iter_draw_slots(today))
    remaining_today = sum(1 for _seq, slot in iter_draw_slots(today) if slot > now)

    recent = list(Draw.objects.all()[:sample])
    freq = frequency_stats(recent)
    series = size_parity_series(recent)
    hot = sorted(freq, key=lambda x: (-x["count"], x["number"]))[:10]
    cold = sorted(freq, key=lambda x: (x["count"], x["number"]))[:10]

    spark = list(reversed(list(Draw.objects.all()[:24])))
    size_total = (series["size_counts"].get("small", 0) + series["size_counts"].get("big", 0)) or 1
    parity_total = (
        series["parity_counts"].get("even", 0)
        + series["parity_counts"].get("odd", 0)
        + series["parity_counts"].get("draw", 0)
    ) or 1

    return {
        "sample_size": len(recent),
        "today_count": today_count,
        "week_count": week_count,
        "scheduled_today": scheduled_today,
        "remaining_today": remaining_today,
        "hot": hot,
        "cold": cold,
        "series": series,
        "size_pct": {
            "small": round(100 * series["size_counts"].get("small", 0) / size_total),
            "big": round(100 * series["size_counts"].get("big", 0) / size_total),
        },
        "parity_pct": {
            "even": round(100 * series["parity_counts"].get("even", 0) / parity_total),
            "odd": round(100 * series["parity_counts"].get("odd", 0) / parity_total),
            "draw": round(100 * series["parity_counts"].get("draw", 0) / parity_total),
        },
        "charts": {
            "size_counts": series["size_counts"],
            "parity_counts": series["parity_counts"],
            "spark_labels": [d.period_code[-3:] for d in spark],
            "spark_totals": [d.total for d in spark],
        },
    }


def size_parity_series(draws) -> dict:
    labels, sizes, parities, totals = [], [], [], []
    size_counts = {"small": 0, "big": 0}
    parity_counts = {"even": 0, "odd": 0, "draw": 0}
    for draw in reversed(list(draws)):
        labels.append(draw.period_code[-3:])
        sizes.append(1 if draw.size == Draw.SIZE_BIG else 0)
        parity_map = {Draw.PARITY_EVEN: 1, Draw.PARITY_ODD: -1, Draw.PARITY_DRAW: 0}
        parities.append(parity_map.get(draw.parity, 0))
        totals.append(draw.total)
        size_counts[draw.size] = size_counts.get(draw.size, 0) + 1
        parity_counts[draw.parity] = parity_counts.get(draw.parity, 0) + 1
    return {
        "labels": labels,
        "sizes": sizes,
        "parities": parities,
        "totals": totals,
        "size_counts": size_counts,
        "parity_counts": parity_counts,
    }


# --- POS TV helpers (count-based Lớn/Nhỏ like the retail screens) ---

TV_BIG_MIN = 41  # numbers 41–80 are LỚN on the POS board


def appearance_order(draw: Draw) -> list[int]:
    """Stable shuffle so live-draw animation is not strictly sorted."""
    nums = list(draw.numbers or [])
    random.Random(draw.period_code).shuffle(nums)
    return nums


def tv_ball_stats(numbers: list[int]) -> dict:
    nums = list(numbers or [])
    big = sum(1 for n in nums if n >= TV_BIG_MIN)
    small = len(nums) - big
    even = sum(1 for n in nums if n % 2 == 0)
    odd = len(nums) - even
    if big > small:
        size_key, size_label, size_count = "big", "LỚN", big
    elif small > big:
        size_key, size_label, size_count = "small", "NHỎ", small
    else:
        size_key, size_label, size_count = "draw", "HOÀ", 10
    if even > odd:
        parity_key, parity_label, parity_count = "even", "CHẴN", even
    elif odd > even:
        parity_key, parity_label, parity_count = "odd", "LẺ", odd
    else:
        parity_key, parity_label, parity_count = "draw", "HOÀ", 10
    return {
        "big": big,
        "small": small,
        "even": even,
        "odd": odd,
        "size_key": size_key,
        "size_label": size_label,
        "size_count": size_count,
        "parity_key": parity_key,
        "parity_label": parity_label,
        "parity_count": parity_count,
    }


def period_display(draw: Draw) -> str:
    return f"#{draw.draw_date:%y%m%d}{draw.sequence:03d}"


def serialize_draw_tv(draw: Draw) -> dict:
    stats = tv_ball_stats(draw.numbers or [])
    appear = appearance_order(draw)
    return {
        "period_code": draw.period_code,
        "period_display": period_display(draw),
        "drawn_at": timezone.localtime(draw.drawn_at).strftime("%H:%M %d/%m"),
        "numbers": appear,
        "numbers_sorted": draw.numbers_sorted,
        **stats,
    }


def _size_chart_point(big: int, small: int) -> dict:
    if big > small:
        return {"y": 2, "n": big, "color": "#FFD000"}
    if small > big:
        return {"y": 0, "n": small, "color": "#16A34A"}
    return {"y": 1, "n": 10, "color": "#111111"}


def _parity_chart_point(even: int, odd: int) -> dict:
    if even >= 13:
        return {"y": 4, "n": even, "color": "#E31C23"}
    if even >= 11:
        return {"y": 3, "n": even, "color": "#E31C23"}
    if even == 10:
        return {"y": 2, "n": 10, "color": "#111111"}
    if odd >= 13:
        return {"y": 0, "n": odd, "color": "#22C55E"}
    return {"y": 1, "n": odd, "color": "#22C55E"}


def consecutive_streaks(draws_newest_first, hit_limit: int = 7, miss_limit: int = 10) -> tuple[list, list]:
    """Hit/miss streaks counted from the most recent draw backwards."""
    hits, misses = [], []
    rows = list(draws_newest_first)
    for n in POOL:
        hit = 0
        for draw in rows:
            if n in (draw.numbers or []):
                hit += 1
            else:
                break
        miss = 0
        for draw in rows:
            if n not in (draw.numbers or []):
                miss += 1
            else:
                break
        if hit >= 2:
            hits.append({"number": n, "count": hit})
        if miss >= 1:
            misses.append({"number": n, "count": miss})
    hits.sort(key=lambda x: (-x["count"], x["number"]))
    misses.sort(key=lambda x: (-x["count"], x["number"]))
    return hits[:hit_limit], misses[:miss_limit]


def _top_freq(draws, hot: bool, limit: int = 10) -> list[dict]:
    freq = frequency_stats(draws)
    if hot:
        ordered = sorted(freq, key=lambda x: (-x["count"], x["number"]))
    else:
        ordered = sorted(freq, key=lambda x: (x["count"], x["number"]))
    return [{"number": x["number"], "count": x["count"]} for x in ordered[:limit]]


def pos_tv_payload() -> dict:
    """JSON-ready payload for the POS / draw-area TV simulator."""
    ensure_draws_up_to_now(lookback_days=2)
    nxt = next_draw_at()
    now = timezone.localtime()
    recent = list(Draw.objects.all()[:100])
    latest = recent[0] if recent else None
    chart_src = list(reversed(recent[:22]))
    size_pts = []
    parity_pts = []
    for draw in chart_src:
        st = tv_ball_stats(draw.numbers or [])
        size_pts.append(_size_chart_point(st["big"], st["small"]))
        parity_pts.append(_parity_chart_point(st["even"], st["odd"]))
    last5 = recent[:5]
    hit_streaks, miss_streaks = consecutive_streaks(recent)
    next_hm = timezone.localtime(nxt).strftime("%H:%M") if nxt else ""
    next_label = f"Lúc {timezone.localtime(nxt).hour}h" if nxt else ""
    cd = countdown_seconds(now)
    return {
        "countdown": cd,
        "countdown_label": f"{cd // 60:02d}:{cd % 60:02d}",
        "next_draw": next_hm,
        "next_draw_label": next_label,
        "latest": serialize_draw_tv(latest) if latest else None,
        "current_period": latest.period_code if latest else "",
        "current_display": period_display(latest) if latest else "",
        "recent3": [serialize_draw_tv(d) for d in recent[:3]],
        "chart_size": {
            "values": [p["y"] for p in size_pts],
            "counts": [p["n"] for p in size_pts],
            "colors": [p["color"] for p in size_pts],
        },
        "chart_parity": {
            "values": [p["y"] for p in parity_pts],
            "counts": [p["n"] for p in parity_pts],
            "colors": [p["color"] for p in parity_pts],
        },
        "hot5": _top_freq(last5, hot=True),
        "hot100": _top_freq(recent, hot=True),
        "cold5": _top_freq(last5, hot=False),
        "cold100": _top_freq(recent, hot=False),
        "hit_streaks": hit_streaks,
        "miss_streaks": miss_streaks,
        "sample5": len(last5),
        "sample100": len(recent),
    }
