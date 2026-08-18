"""Keno prize table for Chơi thử (simulation, no real payout).

Source: VTCPay prize-rules article (mệnh giá 10.000 ₫ / lần):
https://vtcpay.vn/tin-tuc-473/tin-tu-vtc-pay-28/mua-ve-so-keno-tai-vtcpay-thanh-dai-gia-sau-10phut-45938
Basic matrix from the article image ``keno.png``.

Supplementary Lớn/Nhỏ and Chẵn/Lẻ amounts are not on that page; they come from
the same publisher's prize-structure article:
https://vtcpay.vn/tin-tuc-473/tin-tu-vtc-pay-28/co-cau-giai-thuong-keno-vietlott-66274
"""

from __future__ import annotations

STAKE_VND = 10_000

# pick_count -> {match_count: amount_vnd}
BASIC_PAYOUTS: dict[int, dict[int, int]] = {
    1: {1: 20_000},
    2: {2: 90_000},
    3: {2: 20_000, 3: 200_000},
    4: {2: 10_000, 3: 50_000, 4: 400_000},
    5: {3: 10_000, 4: 150_000, 5: 4_400_000},
    6: {3: 10_000, 4: 40_000, 5: 450_000, 6: 12_500_000},
    7: {3: 10_000, 4: 20_000, 5: 100_000, 6: 1_200_000, 7: 40_000_000},
    8: {0: 10_000, 4: 10_000, 5: 50_000, 6: 500_000, 7: 5_000_000, 8: 200_000_000},
    9: {0: 10_000, 4: 10_000, 5: 30_000, 6: 150_000, 7: 1_500_000, 8: 12_000_000, 9: 800_000_000},
    10: {
        0: 10_000,
        5: 20_000,
        6: 80_000,
        7: 600_000,
        8: 7_400_000,
        9: 150_000_000,
        10: 2_000_000_000,
    },
}

SIZE_PRIZE_13 = 56_000
PARITY_PRIZE_13_14 = 40_000
PARITY_PRIZE_15 = 210_000

SIM_NOTE = "Mô phỏng trên Chơi thử — không chi trả tiền thật."


def format_vnd(amount: int) -> str:
    grouped = f"{int(amount):,}".replace(",", ".")
    return f"{grouped} ₫"


def basic_amount(pick_count: int, match_count: int) -> int:
    return BASIC_PAYOUTS.get(pick_count, {}).get(match_count, 0)


def _result(
    *,
    won: bool,
    amount: int,
    name: str,
    detail: str,
    extra: dict | None = None,
) -> dict:
    payload = {
        "won": won,
        "amount": amount,
        "amount_label": format_vnd(amount) if amount else "0 ₫",
        "name": name,
        "detail": detail,
        "headline": "Trúng thưởng" if won else "Không trúng",
        "note": SIM_NOTE,
    }
    if extra:
        payload.update(extra)
    return payload


def evaluate_basic(picked: list[int], drawn: list[int]) -> dict:
    picks = sorted({n for n in picked if 1 <= n <= 80})[:10]
    pick_count = len(picks)
    matched = sorted(set(picks) & set(drawn))
    match_count = len(matched)
    if pick_count == 0:
        return _result(
            won=False,
            amount=0,
            name="Cách chơi cơ bản",
            detail="Chưa chọn số nên chưa đối chiếu giải cơ bản.",
            extra={
                "pick_count": 0,
                "match_count": 0,
                "headline": "Chưa chọn số",
            },
        )
    amount = basic_amount(pick_count, match_count)
    if amount:
        detail = f"Bậc {pick_count} · trùng {match_count} số · mệnh giá {format_vnd(STAKE_VND)}."
    else:
        detail = f"Bậc {pick_count} · trùng {match_count} số — không có giải trên bảng thưởng."
    return _result(
        won=amount > 0,
        amount=amount,
        name=f"Cách chơi cơ bản · Bậc {pick_count}",
        detail=detail,
        extra={"pick_count": pick_count, "match_count": match_count},
    )


def evaluate_size(drawn: list[int]) -> dict:
    from .services import tv_ball_stats

    stats = tv_ball_stats(drawn)
    key = stats["size_key"]
    count = stats["size_count"]
    if key in ("big", "small") and count >= 13:
        label = "Lớn" if key == "big" else "Nhỏ"
        span = "41–80" if key == "big" else "01–40"
        return _result(
            won=True,
            amount=SIZE_PRIZE_13,
            name=f"Lớn / Nhỏ · {label} 13+",
            detail=f"{count} số trong {span} (cần từ 13 số).",
            extra={"size_key": key, "size_count": count},
        )
    if key == "draw":
        detail = "Hòa 10–10 — bảng này chưa có giải Hòa Lớn/Nhỏ."
    else:
        label = "Lớn" if key == "big" else "Nhỏ"
        detail = f"Kỳ này {label} {count} số — giải Lớn/Nhỏ bắt đầu từ 13 số."
    return _result(
        won=False,
        amount=0,
        name="Lớn / Nhỏ",
        detail=detail,
        extra={"size_key": key, "size_count": count},
    )


def evaluate_parity(drawn: list[int]) -> dict:
    even = sum(1 for n in drawn if n % 2 == 0)
    odd = len(drawn) - even
    if even >= 15:
        return _result(
            won=True,
            amount=PARITY_PRIZE_15,
            name="Chẵn / Lẻ · Chẵn 15+",
            detail=f"{even} số chẵn trong 20 số quay.",
            extra={"parity_key": "even", "parity_count": even},
        )
    if even >= 13:
        return _result(
            won=True,
            amount=PARITY_PRIZE_13_14,
            name="Chẵn / Lẻ · Chẵn 13–14",
            detail=f"{even} số chẵn trong 20 số quay.",
            extra={"parity_key": "even", "parity_count": even},
        )
    if odd >= 15:
        return _result(
            won=True,
            amount=PARITY_PRIZE_15,
            name="Chẵn / Lẻ · Lẻ 15+",
            detail=f"{odd} số lẻ trong 20 số quay.",
            extra={"parity_key": "odd", "parity_count": odd},
        )
    if odd >= 13:
        return _result(
            won=True,
            amount=PARITY_PRIZE_13_14,
            name="Chẵn / Lẻ · Lẻ 13–14",
            detail=f"{odd} số lẻ trong 20 số quay.",
            extra={"parity_key": "odd", "parity_count": odd},
        )
    if even == 10:
        detail = "Hòa 10–10 — bảng này chưa có giải Hòa Chẵn/Lẻ."
        key, count = "draw", 10
    elif even > odd:
        detail = f"Kỳ này {even} số chẵn — giải Chẵn bắt đầu từ 13 số."
        key, count = "even", even
    else:
        detail = f"Kỳ này {odd} số lẻ — giải Lẻ bắt đầu từ 13 số."
        key, count = "odd", odd
    return _result(
        won=False,
        amount=0,
        name="Chẵn / Lẻ",
        detail=detail,
        extra={"parity_key": key, "parity_count": count},
    )


def _side_popup_lines(size: dict, parity: dict) -> list[str]:
    lines = []
    if size.get("won"):
        label = "Lớn" if size.get("size_key") == "big" else "Nhỏ"
        lines.append(f"Cửa {label} — {size.get('amount_label', '0 ₫')}")
    if parity.get("won"):
        label = "Chẵn" if parity.get("parity_key") == "even" else "Lẻ"
        lines.append(f"Cửa {label} — {parity.get('amount_label', '0 ₫')}")
    return lines


def sim_popup(basic: dict, size: dict, parity: dict) -> dict:
    """Copy for the Chơi thử prize popup and the post-dismiss notice zone."""
    match_count = int(basic.get("match_count") or 0)
    total = int(basic.get("amount") or 0) + int(size.get("amount") or 0) + int(parity.get("amount") or 0)
    won = total > 0
    sides = _side_popup_lines(size, parity)
    if won:
        title = "Chúc mừng bạn đã thắng"
        if basic.get("won"):
            parts = [f"Trùng {match_count} số — {basic.get('amount_label', '0 ₫')}"]
        else:
            parts = [f"Trùng {match_count} số"]
        parts.extend(sides)
        body = ". ".join(parts) + "."
        notice_lead = f"Trúng thưởng · trùng {match_count} số · {format_vnd(total)}"
    else:
        title = "Chúc may mắn lần sau"
        body = ""
        notice_lead = f"Không trúng · trùng {match_count} số"
    return {
        "won": won,
        "total_amount": total,
        "total_amount_label": format_vnd(total) if total else "0 ₫",
        "popup_title": title,
        "popup_body": body,
        "notice_title": "Kết quả kỳ quay vừa rồi",
        "notice_lead": notice_lead,
    }


def evaluate_sim(picked: list[int], drawn: list[int]) -> dict:
    basic = evaluate_basic(picked, drawn)
    size = evaluate_size(drawn)
    parity = evaluate_parity(drawn)
    return {
        "basic": basic,
        "size": size,
        "parity": parity,
        "stake": STAKE_VND,
        "stake_label": format_vnd(STAKE_VND),
        "note": SIM_NOTE,
        **sim_popup(basic, size, parity),
    }


def basic_table_view() -> dict:
    picks = list(range(10, 0, -1))
    matches = list(range(10, -1, -1))
    rows = []
    for match in matches:
        cells = []
        for pick in picks:
            amount = BASIC_PAYOUTS.get(pick, {}).get(match)
            cells.append(
                {
                    "pick": pick,
                    "match": match,
                    "amount": amount,
                    "label": format_vnd(amount) if amount else "—",
                }
            )
        rows.append({"match": match, "cells": cells})
    return {"picks": picks, "rows": rows}


SIDE_PRIZE_ROWS = [
    {
        "name": "Lớn",
        "rule": "Từ 13 số trong 41–80",
        "amount": SIZE_PRIZE_13,
        "amount_label": format_vnd(SIZE_PRIZE_13),
    },
    {
        "name": "Nhỏ",
        "rule": "Từ 13 số trong 01–40",
        "amount": SIZE_PRIZE_13,
        "amount_label": format_vnd(SIZE_PRIZE_13),
    },
    {
        "name": "Chẵn / Lẻ",
        "rule": "13 hoặc 14 số chẵn (hoặc lẻ)",
        "amount": PARITY_PRIZE_13_14,
        "amount_label": format_vnd(PARITY_PRIZE_13_14),
    },
    {
        "name": "Chẵn / Lẻ",
        "rule": "15 số trở lên chẵn (hoặc lẻ)",
        "amount": PARITY_PRIZE_15,
        "amount_label": format_vnd(PARITY_PRIZE_15),
    },
]
