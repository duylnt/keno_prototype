"""KPI report builder matching the project PDF growth funnel and KPI sections."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from django.db.models import Avg, Count, Q
from django.http import HttpRequest
from django.utils import timezone

from apps.community.models import CommunityPost, MinigameEvent
from apps.content.models import Article
from apps.locations.models import ExperienceCode, PosLocation

from .models import (
    AnalyticsEvent,
    CommunityKpiSnapshot,
    GA4Snapshot,
    GSCQuery,
    GSCSnapshot,
    TechnicalKpiSnapshot,
)

PRESETS = {
    "7": 7,
    "30": 30,
    "90": 90,
}


def parse_date_range(request: HttpRequest | None = None) -> tuple[date, date, str]:
    today = timezone.localdate()
    preset = "30"
    if request is not None:
        preset = (request.GET.get("range") or "30").strip()
        start_raw = (request.GET.get("start") or "").strip()
        end_raw = (request.GET.get("end") or "").strip()
        if start_raw and end_raw:
            try:
                start = date.fromisoformat(start_raw)
                end = date.fromisoformat(end_raw)
                if start > end:
                    start, end = end, start
                return start, end, "custom"
            except ValueError:
                pass
        if preset == "month":
            start = today.replace(day=1)
            return start, today, "month"
    days = PRESETS.get(preset, 30)
    preset = preset if preset in PRESETS or preset == "month" else "30"
    return today - timedelta(days=days - 1), today, preset


def _count(qs, name: str) -> int:
    return qs.filter(event_name=name).count()


def _unique(qs, name: str) -> int:
    return qs.filter(event_name=name).exclude(session_key="").values("session_key").distinct().count()


def _pct(part: float, whole: float, digits: int = 1) -> float:
    if not whole:
        return 0.0
    return round(100.0 * part / whole, digits)


def _metric_sum(rows: list, attr: str) -> int:
    return int(sum(getattr(r, attr, 0) or 0 for r in rows))


def _metric_avg(rows: list, attr: str, digits: int = 1) -> float:
    if not rows:
        return 0.0
    return round(sum(getattr(r, attr, 0) or 0 for r in rows) / len(rows), digits)


def _ga4_in(start: date, end: date):
    return GA4Snapshot.objects.filter(date__gte=start, date__lte=end).order_by("date")


def build_kpi_report(request: HttpRequest | None = None) -> dict[str, Any]:
    """Full CMS report payload. Default window is the last 30 days."""
    start, end, preset = parse_date_range(request)
    span_days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=span_days - 1)

    events = AnalyticsEvent.objects.filter(occurred_at__date__gte=start, occurred_at__date__lte=end)
    prev_events = AnalyticsEvent.objects.filter(
        occurred_at__date__gte=prev_start, occurred_at__date__lte=prev_end
    )
    sessions = events.exclude(session_key="").values("session_key").distinct().count()
    sessions_safe = sessions or 1

    ga4_rows = list(_ga4_in(start, end))
    ga4_prev = list(_ga4_in(prev_start, prev_end))
    gsc_rows = list(GSCSnapshot.objects.filter(date__gte=start, date__lte=end).order_by("date"))
    gsc_prev = list(GSCSnapshot.objects.filter(date__gte=prev_start, date__lte=prev_end).order_by("date"))
    latest_ga4 = ga4_rows[-1] if ga4_rows else GA4Snapshot.objects.order_by("-date").first()
    latest_gsc = gsc_rows[-1] if gsc_rows else GSCSnapshot.objects.order_by("-date").first()

    organic = _metric_sum(ga4_rows, "organic_sessions")
    organic_prev = _metric_sum(ga4_prev, "organic_sessions")
    prev_coverage = len(ga4_prev)
    curr_coverage = len(ga4_rows)
    if organic_prev and prev_coverage >= max(3, int(curr_coverage * 0.5)):
        organic_growth = _pct(organic - organic_prev, organic_prev)
        organic_growth_ok = organic_growth >= 15
    else:
        organic_growth = None
        organic_growth_ok = False
    referral = _metric_sum(ga4_rows, "referral_sessions")
    impressions = _metric_sum(gsc_rows, "impressions")
    gsc_clicks = _metric_sum(gsc_rows, "clicks")
    new_users = _metric_sum(ga4_rows, "new_users")
    active_users = _metric_sum(ga4_rows, "active_users")
    ga4_sessions = _metric_sum(ga4_rows, "sessions")
    returning_users = _metric_sum(ga4_rows, "returning_users")

    result_users = _unique(events, AnalyticsEvent.RESULT_VIEW)
    stats_views = _count(events, AnalyticsEvent.STATS_VIEW)
    ticket_checks = _count(events, AnalyticsEvent.TICKET_CHECK)
    simulator = _count(events, AnalyticsEvent.SIMULATOR_PLAY)
    find_pos = _count(events, AnalyticsEvent.FIND_POS_CLICK)
    pos_search = _count(events, AnalyticsEvent.POS_SEARCH)
    pos_detail = _count(events, AnalyticsEvent.POS_DETAIL)
    directions = _count(events, AnalyticsEvent.GET_DIRECTIONS)
    loc_perm = _count(events, AnalyticsEvent.LOCATION_PERMISSION)
    community_cta = _count(events, AnalyticsEvent.COMMUNITY_CTA)
    join_intent = _count(events, AnalyticsEvent.COMMUNITY_JOIN_INTENT)
    voucher_issue = _count(events, AnalyticsEvent.VOUCHER_ISSUE)

    find_pos_ctr = _pct(find_pos, sessions_safe)
    loc_perm_rate = _pct(loc_perm, find_pos or sessions_safe)
    directions_ctr = _pct(directions, pos_detail or sessions_safe)
    pos_intent_sessions = (
        events.filter(
            event_name__in=[
                AnalyticsEvent.FIND_POS_CLICK,
                AnalyticsEvent.POS_SEARCH,
                AnalyticsEvent.POS_DETAIL,
                AnalyticsEvent.GET_DIRECTIONS,
                AnalyticsEvent.LOCATION_PERMISSION,
            ]
        )
        .exclude(session_key="")
        .values("session_key")
        .distinct()
        .count()
    )
    pos_intent_rate = _pct(pos_intent_sessions, sessions_safe)

    returning_pct = _pct(returning_users, active_users) if active_users else 0.0
    d7 = _metric_avg(ga4_rows, "d7_retention")
    d30 = _metric_avg(ga4_rows, "d30_retention")
    pages_per_session = _metric_avg(ga4_rows, "pages_per_session", 2)
    sessions_per_user = round(ga4_sessions / active_users, 2) if active_users else 0.0

    top10 = (
        GSCQuery.objects.filter(date__gte=start, date__lte=end, position__lte=10)
        .values("query")
        .distinct()
        .count()
    )
    query_map: dict[str, dict] = {}
    for row in GSCQuery.objects.filter(date__gte=start, date__lte=end).order_by("-clicks"):
        bucket = query_map.setdefault(
            row.query,
            {"query": row.query, "clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0, "n": 0},
        )
        bucket["clicks"] += row.clicks
        bucket["impressions"] += row.impressions
        bucket["position"] += row.position
        bucket["n"] += 1
    top_queries = []
    for bucket in query_map.values():
        n = bucket["n"] or 1
        impr = bucket["impressions"] or 1
        top_queries.append(
            {
                "query": bucket["query"],
                "clicks": bucket["clicks"],
                "impressions": bucket["impressions"],
                "ctr": round(100.0 * bucket["clicks"] / impr, 2),
                "position": round(bucket["position"] / n, 1),
            }
        )
    top_queries.sort(key=lambda q: (-q["clicks"], q["position"]))
    top_queries = top_queries[:20]

    posts = CommunityPost.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    approved = posts.filter(status=CommunityPost.STATUS_APPROVED).count()
    rejected = posts.filter(status=CommunityPost.STATUS_REJECTED).count()
    pending = CommunityPost.objects.filter(status=CommunityPost.STATUS_PENDING).count()
    total_mod = approved + rejected
    spam_rate = _pct(rejected, total_mod)
    scam_removed = posts.filter(
        status=CommunityPost.STATUS_REJECTED,
    ).filter(
        Q(rejection_reason__icontains="bán")
        | Q(rejection_reason__icontains="spam")
        | Q(rejection_reason__icontains="môi giới")
        | Q(rejection_reason__icontains="scam")
    ).count()
    avg_comments = posts.filter(status=CommunityPost.STATUS_APPROVED).aggregate(
        avg=Avg("comment_count")
    )["avg"] or 0
    moderated = CommunityPost.objects.filter(
        moderated_at__isnull=False,
        created_at__date__gte=start,
        created_at__date__lte=end,
    )
    sla_hours = 0.0
    sla_n = 0
    for post in moderated.only("created_at", "moderated_at"):
        if post.moderated_at and post.created_at:
            sla_hours += (post.moderated_at - post.created_at).total_seconds() / 3600
            sla_n += 1
    sla_hours = round(sla_hours / sla_n, 1) if sla_n else 0.0
    approved_per_day = round(approved / span_days, 1) if span_days else approved

    minigames = MinigameEvent.objects.filter(scheduled_at__date__gte=start, scheduled_at__date__lte=end)
    minigame_participants = sum(e.participants for e in minigames)
    minigame_events = minigames.count()

    comm_rows = list(
        CommunityKpiSnapshot.objects.filter(date__gte=start, date__lte=end).order_by("date")
    )
    new_members = _metric_sum(comm_rows, "new_members")
    authentic_rate = _metric_avg(comm_rows, "authentic_account_rate")
    returning_members = _metric_avg(comm_rows, "returning_active_pct")

    tech = (
        TechnicalKpiSnapshot.objects.filter(date__gte=start, date__lte=end).order_by("-date").first()
        or TechnicalKpiSnapshot.objects.order_by("-date").first()
    )

    o2o_issued = ExperienceCode.objects.filter(created_at__date__gte=start, created_at__date__lte=end).count()
    o2o_redeemed = ExperienceCode.objects.filter(
        redeemed_at__date__gte=start, redeemed_at__date__lte=end
    ).count()
    o2o_rate = _pct(o2o_redeemed, o2o_issued)

    maku = sessions
    result_checks_total = _count(events, AnalyticsEvent.RESULT_VIEW)
    pos_intent_total = find_pos + directions

    funnel = [
        {
            "stage": "Nhận biết",
            "hint": "Hiển thị tìm kiếm, người dùng tự nhiên, người dùng mới",
            "primary": impressions,
            "metrics": [
                {"label": "Impressions Search Console", "value": impressions, "source": "GSC"},
                {"label": "Người dùng mới (GA4)", "value": new_users, "source": "GA4"},
                {"label": "Người dùng organic (phiên organic)", "value": organic, "source": "GA4"},
            ],
        },
        {
            "stage": "Tiếp cận",
            "hint": "Phiên tự nhiên và kênh giới thiệu",
            "primary": organic + referral,
            "metrics": [
                {"label": "Phiên organic", "value": organic, "source": "GA4"},
                {"label": "Phiên referral", "value": referral, "source": "GA4"},
                {"label": "Tổng phiên GA4", "value": ga4_sessions, "source": "GA4"},
            ],
        },
        {
            "stage": "Kích hoạt",
            "hint": "Xem kết quả, tra cứu thống kê, dò vé",
            "primary": result_users,
            "metrics": [
                {"label": "Người dùng xem kết quả", "value": result_users, "source": "Nội bộ"},
                {"label": "Lượt xem thống kê", "value": stats_views, "source": "Nội bộ"},
                {"label": "Lượt dò vé", "value": ticket_checks, "source": "Nội bộ"},
            ],
        },
        {
            "stage": "Gắn kết",
            "hint": "Số phiên/người dùng, số trang/phiên, cộng đồng",
            "primary": community_cta + join_intent,
            "metrics": [
                {"label": "Số phiên / người dùng", "value": sessions_per_user, "source": "GA4"},
                {"label": "Số trang / phiên", "value": pages_per_session, "source": "GA4"},
                {"label": "Chơi thử", "value": simulator, "source": "Nội bộ"},
                {"label": "CTA cộng đồng", "value": community_cta, "source": "Nội bộ"},
                {"label": "Ý định tham gia nhóm", "value": join_intent, "source": "Nội bộ"},
            ],
        },
        {
            "stage": "Giữ chân",
            "hint": "Quay lại sau 7 ngày và 30 ngày",
            "primary": returning_pct,
            "metrics": [
                {"label": "Returning users %", "value": returning_pct, "source": "GA4"},
                {"label": "Giữ chân D7 %", "value": d7, "source": "GA4"},
                {"label": "Giữ chân D30 %", "value": d30, "source": "GA4"},
            ],
        },
        {
            "stage": "Ý định offline",
            "hint": "Tìm điểm bán, vị trí, chỉ đường",
            "primary": pos_intent_sessions,
            "metrics": [
                {"label": "Find POS CTR (%)", "value": find_pos_ctr, "source": "Nội bộ"},
                {"label": "Người dùng tìm điểm bán", "value": pos_search, "source": "Nội bộ"},
                {"label": "Xem chi tiết điểm bán", "value": pos_detail, "source": "Nội bộ"},
                {"label": "Cấp quyền vị trí", "value": loc_perm, "source": "Nội bộ"},
                {"label": "Location permission rate (%)", "value": loc_perm_rate, "source": "Nội bộ"},
                {"label": "Nhấp Chỉ đường", "value": directions, "source": "Nội bộ"},
                {"label": "Get Directions CTR (%)", "value": directions_ctr, "source": "Nội bộ"},
                {"label": "Tỷ lệ ý định digital → POS (%)", "value": pos_intent_rate, "source": "Nội bộ"},
            ],
        },
        {
            "stage": "O2O",
            "hint": "Mã trải nghiệm quét tại POS",
            "primary": o2o_redeemed,
            "metrics": [
                {"label": "Mã O2O phát hành", "value": o2o_issued, "source": "Nội bộ"},
                {"label": "Mã đã quét tại POS", "value": o2o_redeemed, "source": "Nội bộ"},
                {"label": "Tỷ lệ quét mã (%)", "value": o2o_rate, "source": "Nội bộ"},
            ],
        },
    ]

    funnel_max = max((float(s["primary"] or 0) for s in funnel), default=1) or 1
    for stage in funnel:
        stage["bar"] = round(100.0 * float(stage["primary"] or 0) / funnel_max, 1)

    funnel_chart = [
        {"stage": "Xem kết quả", "primary": result_users},
        {"stage": "Cộng đồng", "primary": community_cta + join_intent},
        {"stage": "Ý định POS", "primary": pos_intent_sessions},
        {"stage": "O2O đã quét", "primary": o2o_redeemed},
    ]

    articles_in_range = Article.objects.filter(
        published_at__date__gte=start, published_at__date__lte=end, is_published=True
    ).count()

    internal_counts = dict(
        events.values_list("event_name").annotate(c=Count("id")).values_list("event_name", "c")
    )

    return {
        "date_start": start,
        "date_end": end,
        "date_preset": preset,
        "span_days": span_days,
        "prev_start": prev_start,
        "prev_end": prev_end,
        "north_star": {
            "label": "MAKU",
            "value": maku,
            "supporting": {
                "returning_pct": returning_pct,
                "result_checks": result_checks_total,
                "pos_intent": pos_intent_total,
                "ga4_active": active_users,
            },
        },
        "funnel": funnel,
        "funnel_chart": funnel_chart,
        "website_kpis": {
            "organic_traffic": organic,
            "organic_growth": organic_growth,
            "has_organic_growth": organic_growth is not None,
            "organic_growth_target": "≥15–20%/kỳ so sánh",
            "organic_growth_ok": organic_growth_ok,
            "keyword_top10": top10,
            "result_check_users": result_users,
            "returning_pct": returning_pct,
            "d7": d7,
            "d30": d30,
            "find_pos_ctr": find_pos_ctr,
            "loc_perm_rate": loc_perm_rate,
            "directions_ctr": directions_ctr,
            "mobile_perf_target": "> 90",
            "realtime_latency_target": "< 3 giây",
            "articles_published": articles_in_range,
        },
        "community_kpis": {
            "new_members": new_members,
            "authentic_rate": authentic_rate,
            "authentic_target": 90,
            "approved": approved,
            "approved_per_day": approved_per_day,
            "pending": pending,
            "rejected": rejected,
            "spam_removal_rate": spam_rate,
            "scam_removed": scam_removed,
            "avg_comments": round(avg_comments, 1),
            "returning_active_pct": returning_members,
            "minigame_participants": minigame_participants,
            "minigame_events": minigame_events,
            "moderation_sla_hours": sla_hours,
        },
        "technical": {
            "mobile_perf_score": tech.mobile_perf_score if tech else 0,
            "lcp_ms": tech.lcp_ms if tech else 0,
            "inp_ms": tech.inp_ms if tech else 0,
            "cls": tech.cls if tech else 0,
            "realtime_latency_ms": tech.realtime_latency_ms if tech else 0,
            "cwv_pass": tech.cwv_pass if tech else False,
            "date": tech.date if tech else None,
            "mobile_ok": (tech.mobile_perf_score >= 90) if tech else False,
            "latency_ok": (tech.realtime_latency_ms < 3000) if tech else False,
        },
        "o2o": {
            "issued": o2o_issued,
            "redeemed": o2o_redeemed,
            "rate": o2o_rate,
            "find_pos": find_pos,
            "pos_search": pos_search,
            "pos_detail": pos_detail,
            "directions": directions,
            "loc_perm": loc_perm,
            "find_pos_ctr": find_pos_ctr,
            "loc_perm_rate": loc_perm_rate,
            "directions_ctr": directions_ctr,
            "intent_rate": pos_intent_rate,
            "intent_sessions": pos_intent_sessions,
            "pos_count": PosLocation.objects.filter(is_active=True).count(),
            "recent_codes": list(
                ExperienceCode.objects.filter(created_at__date__gte=start, created_at__date__lte=end).order_by(
                    "-created_at"
                )[:12]
            ),
        },
        "ga4_series": [
            {
                "date": r.date.isoformat(),
                "active": r.active_users,
                "organic": r.organic_sessions,
                "new": r.new_users,
                "returning": r.returning_users,
                "sessions": r.sessions,
            }
            for r in ga4_rows
        ],
        "gsc_series": [
            {
                "date": r.date.isoformat(),
                "clicks": r.clicks,
                "impressions": r.impressions,
                "position": r.position,
                "ctr": r.ctr,
            }
            for r in gsc_rows
        ],
        "top_queries": top_queries,
        "latest_ga4": latest_ga4,
        "latest_gsc": latest_gsc,
        "internal_counts": internal_counts,
        "ga4_totals": {
            "active_users": active_users,
            "new_users": new_users,
            "returning_users": returning_users,
            "sessions": ga4_sessions,
            "organic": organic,
            "referral": referral,
            "pages_per_session": pages_per_session,
            "sessions_per_user": sessions_per_user,
        },
        "gsc_totals": {
            "clicks": gsc_clicks,
            "impressions": impressions,
            "ctr": round(100.0 * gsc_clicks / impressions, 2) if impressions else 0,
            "position": _metric_avg(gsc_rows, "position", 1),
        },
        "event_bars": [
            {"name": label, "key": key, "value": internal_counts.get(key, 0)}
            for key, label in AnalyticsEvent.EVENT_CHOICES
        ],
        "prev_events_sessions": prev_events.exclude(session_key="").values("session_key").distinct().count(),
    }
