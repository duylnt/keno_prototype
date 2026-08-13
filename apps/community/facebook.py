"""Official Facebook Graph API helpers. Never scrape Page HTML. Never log tokens."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.core.models import SiteSettings

from .models import FacebookPagePost

logger = logging.getLogger(__name__)

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

READ_PERMISSIONS = "pages_read_engagement"
MANAGE_PERMISSIONS = "pages_manage_posts"


class FacebookAPIError(Exception):
    def __init__(self, message: str, code: int | None = None, permission: str = ""):
        super().__init__(message)
        self.code = code
        self.permission = permission


def mask_token(token: str) -> str:
    raw = (token or "").strip()
    if not raw:
        return ""
    if len(raw) <= 8:
        return "••••"
    return f"{raw[:4]}••••{raw[-4:]}"


def _scrub(text: str, token: str = "") -> str:
    value = text or ""
    if token:
        value = value.replace(token, "***")
    for extra in (_cms_token(), _env_token()):
        if extra:
            value = value.replace(extra, "***")
    return value


def _env_token() -> str:
    return (getattr(settings, "FACEBOOK_PAGE_ACCESS_TOKEN", "") or "").strip()


def _cms_token() -> str:
    try:
        return (SiteSettings.load().facebook_page_access_token or "").strip()
    except Exception:
        return ""


def page_access_token() -> str:
    return _cms_token() or _env_token()


def page_id() -> str:
    site = SiteSettings.load()
    return (site.facebook_page_id or getattr(settings, "FACEBOOK_PAGE_ID", "") or "").strip()


def page_url() -> str:
    site = SiteSettings.load()
    return (site.facebook_page_url or getattr(settings, "FACEBOOK_PAGE_URL", "") or "").strip()


def app_id() -> str:
    site = SiteSettings.load()
    return (site.facebook_app_id or getattr(settings, "FACEBOOK_APP_ID", "") or "").strip()


def token_is_configured() -> bool:
    return bool(page_access_token())


def plugin_ready() -> bool:
    return bool(page_url() and app_id())


def facebook_moderation_links(url: str = "") -> dict[str, str]:
    href = (url or page_url()).rstrip("/")
    if not href:
        return {}
    return {
        "page": href,
        "inbox": f"{href}/inbox",
        "published": f"{href}/posts",
        "moderation": "https://www.facebook.com/moderation_tool/",
        "settings": f"{href}/settings/?tab=admin_roles",
    }


def _parse_error(payload: str, token: str) -> FacebookAPIError:
    clean = _scrub(payload, token)
    code = None
    permission = ""
    message = "Graph API không trả lời được."
    try:
        data = json.loads(payload)
        err = data.get("error") or {}
        code = err.get("code")
        message = _scrub(str(err.get("message") or message), token)
        permission = str(err.get("error_subcode") or "")
        lowered = message.lower()
        if "pages_read_engagement" in lowered or code in {10, 200, 294}:
            permission = permission or READ_PERMISSIONS
        if "pages_manage_posts" in lowered or "unpublished" in lowered:
            permission = MANAGE_PERMISSIONS
    except json.JSONDecodeError:
        message = _scrub(payload[:240], token) or message
    return FacebookAPIError(f"Graph API{f' ({code})' if code is not None else ''}: {message}"[:300], code, permission)


def graph_request(path: str, *, method: str = "GET", params: dict | None = None, data: dict | None = None) -> dict:
    token = page_access_token()
    if not token:
        raise FacebookAPIError("Chưa cấu hình Page Access Token (CMS hoặc FACEBOOK_PAGE_ACCESS_TOKEN).")
    query = dict(params or {})
    query["access_token"] = token
    url = f"{GRAPH_BASE}/{path.lstrip('/')}?{urllib.parse.urlencode(query)}"
    body = None
    headers = {"User-Agent": "KenoPrototype/1.0"}
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        method = method or "POST"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise _parse_error(payload, token) from None
    except urllib.error.URLError:
        logger.warning("Facebook Graph API unreachable (token omitted).")
        raise FacebookAPIError("Không kết nối được Graph API.") from None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise FacebookAPIError("Graph API trả về dữ liệu không hợp lệ.") from None


def _parse_created(value: str | None):
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    if len(normalized) >= 5 and normalized[-5] in "+-" and normalized[-3] != ":":
        normalized = f"{normalized[:-2]}:{normalized[-2:]}"
    parsed = parse_datetime(normalized)
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, dt_timezone.utc)
    return parsed


def sync_facebook_page(limit: int = 25) -> dict:
    """Fetch published Page posts into FacebookPagePost. Official API only."""
    pid = page_id()
    if not page_access_token():
        return {
            "ok": False,
            "created": 0,
            "updated": 0,
            "error": "Chưa có Page Access Token. Nhúng Page Plugin vẫn dùng được nếu có URL + App ID.",
            "permission": "",
        }
    if not pid:
        return {
            "ok": False,
            "created": 0,
            "updated": 0,
            "error": "Chưa có Facebook Page ID.",
            "permission": "",
        }
    try:
        payload = graph_request(
            f"{pid}/published_posts",
            params={
                "fields": "id,message,created_time,permalink_url,is_hidden,is_published",
                "limit": str(limit),
            },
        )
    except FacebookAPIError as exc:
        return {
            "ok": False,
            "created": 0,
            "updated": 0,
            "error": str(exc),
            "permission": exc.permission or READ_PERMISSIONS,
        }
    created = updated = 0
    for row in payload.get("data") or []:
        fb_id = str(row.get("id") or "").strip()
        if not fb_id:
            continue
        defaults = {
            "message": (row.get("message") or "").strip(),
            "created_time": _parse_created(row.get("created_time")),
            "permalink": row.get("permalink_url") or "",
            "is_hidden": bool(row.get("is_hidden")),
            "is_published": bool(row.get("is_published", True)),
            "last_api_error": "",
        }
        _, was_created = FacebookPagePost.objects.update_or_create(fb_id=fb_id, defaults=defaults)
        if was_created:
            created += 1
        else:
            updated += 1
    return {"ok": True, "created": created, "updated": updated, "error": "", "permission": ""}


def moderate_cached_post(post: FacebookPagePost, action: str) -> dict:
    """Hide or unpublish via Pages API when the Page token allows it."""
    if action not in {"hide", "unpublish", "show"}:
        return {"ok": False, "error": "Hành động không hợp lệ."}
    data = {}
    if action == "hide":
        data = {"is_hidden": "true"}
    elif action == "unpublish":
        data = {"is_published": "false"}
    elif action == "show":
        data = {"is_hidden": "false", "is_published": "true"}
    try:
        graph_request(post.fb_id, method="POST", data=data)
    except FacebookAPIError as exc:
        post.last_api_error = str(exc)[:300]
        post.save(update_fields=["last_api_error", "synced_at"])
        return {
            "ok": False,
            "error": str(exc),
            "permission": exc.permission or MANAGE_PERMISSIONS,
        }
    if action == "hide":
        post.is_hidden = True
    elif action == "unpublish":
        post.is_published = False
    else:
        post.is_hidden = False
        post.is_published = True
    post.last_api_error = ""
    post.save(update_fields=["is_hidden", "is_published", "last_api_error", "synced_at"])
    return {"ok": True, "error": "", "permission": ""}


def probe_api_status() -> dict:
    """Describe Graph API readiness without exposing the token."""
    token = page_access_token()
    pid = page_id()
    status = {
        "token_configured": bool(token),
        "token_masked": mask_token(token) if token else "",
        "page_id": pid,
        "page_url": page_url(),
        "app_id": app_id(),
        "plugin_ready": plugin_ready(),
        "page_reachable": None,
        "can_read_posts": None,
        "can_manage_posts": None,
        "page_name": "",
        "error": "",
        "hint": "",
    }
    if not token:
        status["hint"] = (
            "Cần Page Access Token (không phải User token) với "
            f"{READ_PERMISSIONS} để đọc bài, {MANAGE_PERMISSIONS} để ẩn/gỡ đăng."
        )
        return status
    if not pid:
        status["error"] = "Thiếu Page ID."
        status["hint"] = "Điền Facebook Page ID trong Cài đặt website."
        return status
    try:
        me = graph_request(pid, params={"fields": "id,name"})
        status["page_reachable"] = True
        status["page_name"] = me.get("name") or ""
    except FacebookAPIError as exc:
        status["page_reachable"] = False
        status["error"] = str(exc)
        status["hint"] = "Token phải là Page token của đúng Page ID."
        return status
    try:
        graph_request(f"{pid}/published_posts", params={"fields": "id", "limit": "1"})
        status["can_read_posts"] = True
    except FacebookAPIError as exc:
        status["can_read_posts"] = False
        status["error"] = str(exc)
        status["hint"] = f"Cấp quyền {READ_PERMISSIONS} cho app / Page token."
        return status
    status["can_manage_posts"] = None
    status["hint"] = (
        f"Đọc bài: OK. Ẩn/gỡ đăng cần {MANAGE_PERMISSIONS} — thử trên một bài cache; "
        "nếu Graph từ chối, CMS sẽ báo lỗi, không giả lập thành công."
    )
    return status
