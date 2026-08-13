"""Google Analytics 4 Data API and Search Console sync helpers."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .models import DailyMetric, GA4Snapshot, GSCQuery, GSCSnapshot

logger = logging.getLogger(__name__)


def _credentials(path: str | None):
    path = path or settings.GSC_CREDENTIALS_PATH
    if not path:
        raise RuntimeError("Chưa cấu hình GOOGLE_APPLICATION_CREDENTIALS / GSC_CREDENTIALS_PATH.")
    if not Path(path).exists():
        raise RuntimeError(f"Không tìm thấy file credentials: {path}")
    from google.oauth2 import service_account

    return path, service_account


def sync_ga4(days: int = 14) -> int:
    """Pull GA4 daily metrics into GA4Snapshot. Returns rows upserted."""
    property_id = settings.GA4_PROPERTY_ID
    if not property_id:
        raise RuntimeError("Chưa cấu hình GA4_PROPERTY_ID.")
    cred_path, service_account = _credentials(settings.GSC_CREDENTIALS_PATH)
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

    credentials = service_account.Credentials.from_service_account_file(
        cred_path,
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    client = BetaAnalyticsDataClient(credentials=credentials)
    end = timezone.localdate()
    start = end - timedelta(days=days)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="screenPageViewsPerSession"),
        ],
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
    )
    response = client.run_report(request)
    organic_req = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date"), Dimension(name="sessionDefaultChannelGroup")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
    )
    organic_map: dict[date, dict] = {}
    organic_resp = client.run_report(organic_req)
    for row in organic_resp.rows:
        day = datetime_from_ga(row.dimension_values[0].value)
        channel = row.dimension_values[1].value
        sessions = int(float(row.metric_values[0].value or 0))
        organic_map.setdefault(day, {"organic": 0, "referral": 0})
        if "Organic" in channel:
            organic_map[day]["organic"] += sessions
        if "Referral" in channel:
            organic_map[day]["referral"] += sessions

    count = 0
    for row in response.rows:
        day = datetime_from_ga(row.dimension_values[0].value)
        metrics = [float(m.value or 0) for m in row.metric_values]
        channels = organic_map.get(day, {})
        obj, _ = GA4Snapshot.objects.update_or_create(
            date=day,
            defaults={
                "active_users": int(metrics[0]),
                "new_users": int(metrics[1]),
                "sessions": int(metrics[2]),
                "engaged_sessions": int(metrics[3]),
                "bounce_rate": round(metrics[4] * 100, 2) if metrics[4] <= 1 else round(metrics[4], 2),
                "avg_session_duration": round(metrics[5], 1),
                "pages_per_session": round(metrics[6], 2),
                "organic_sessions": channels.get("organic", 0),
                "referral_sessions": channels.get("referral", 0),
                "returning_users": max(0, int(metrics[0]) - int(metrics[1])),
            },
        )
        DailyMetric.objects.update_or_create(
            date=day,
            source=DailyMetric.SOURCE_GA4,
            metric_name="active_users",
            defaults={"value": obj.active_users},
        )
        count += 1
    return count


def datetime_from_ga(value: str) -> date:
    return date(int(value[0:4]), int(value[4:6]), int(value[6:8]))


def sync_gsc(days: int = 14) -> tuple[int, int]:
    """Pull Search Console search analytics. Returns (daily_rows, query_rows)."""
    site_url = settings.GSC_SITE_URL
    if not site_url:
        raise RuntimeError("Chưa cấu hình GSC_SITE_URL.")
    cred_path, service_account = _credentials(settings.GSC_CREDENTIALS_PATH)
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_file(
        cred_path,
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
    )
    service = build("searchconsole", "v1", credentials=credentials, cache_discovery=False)
    end = timezone.localdate()
    start = end - timedelta(days=days)
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["date"],
        "rowLimit": 1000,
    }
    data = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    daily = 0
    for row in data.get("rows", []):
        day = date.fromisoformat(row["keys"][0])
        clicks = int(row.get("clicks", 0))
        impressions = int(row.get("impressions", 0))
        ctr = round(float(row.get("ctr", 0)) * 100, 2)
        position = round(float(row.get("position", 0)), 2)
        GSCSnapshot.objects.update_or_create(
            date=day,
            defaults={
                "clicks": clicks,
                "impressions": impressions,
                "ctr": ctr,
                "position": position,
            },
        )
        DailyMetric.objects.update_or_create(
            date=day,
            source=DailyMetric.SOURCE_GSC,
            metric_name="impressions",
            defaults={"value": impressions},
        )
        daily += 1

    qbody = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["date", "query"],
        "rowLimit": 5000,
    }
    qdata = service.searchanalytics().query(siteUrl=site_url, body=qbody).execute()
    queries = 0
    for row in qdata.get("rows", []):
        day = date.fromisoformat(row["keys"][0])
        query = row["keys"][1]
        GSCQuery.objects.update_or_create(
            date=day,
            query=query,
            defaults={
                "clicks": int(row.get("clicks", 0)),
                "impressions": int(row.get("impressions", 0)),
                "ctr": round(float(row.get("ctr", 0)) * 100, 2),
                "position": round(float(row.get("position", 0)), 2),
            },
        )
        queries += 1
    return daily, queries
