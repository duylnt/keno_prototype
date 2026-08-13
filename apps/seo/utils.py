"""URL, slug and HTML helpers for on-site SEO."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.utils.text import slugify

VIET_MAP = str.maketrans(
    "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
    "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ",
    "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"
    "AAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD",
)

_TAG_RE = re.compile(r"<[^>]+>", re.I)
_WS_RE = re.compile(r"\s+")


def site_origin() -> str:
    return (getattr(settings, "SITE_URL", "") or "http://127.0.0.1:8000").rstrip("/")


def site_protocol() -> str:
    return urlparse(site_origin()).scheme or "http"


def absolute_url(path: str) -> str:
    if not path:
        return site_origin() + "/"
    if path.startswith("http://") or path.startswith("https://"):
        return path
    origin = site_origin()
    if not path.startswith("/"):
        path = "/" + path
    return origin + path


def normalize_path(path: str) -> str:
    raw = (path or "").strip()
    if not raw:
        return "/"
    parsed = urlparse(raw)
    path = parsed.path or raw
    if path.startswith("http"):
        path = urlparse(path).path
    if not path.startswith("/"):
        path = "/" + path
    last = path.rsplit("/", 1)[-1]
    if last and "." in last:
        return path
    if not path.endswith("/"):
        path += "/"
    return path


def canonical_for_request(request, override: str = "") -> str:
    if override:
        return absolute_url(override)
    return absolute_url(normalize_path(request.path))


def slugify_vi(value: str, max_length: int = 80) -> str:
    ascii_value = (value or "").translate(VIET_MAP)
    slug = slugify(ascii_value) or "bai-viet"
    return slug[:max_length].strip("-")


def strip_tags(html: str) -> str:
    text = _TAG_RE.sub(" ", html or "")
    return _WS_RE.sub(" ", text).strip()


def first_paragraph(html: str) -> str:
    match = re.search(r"<p\b[^>]*>(.*?)</p>", html or "", re.I | re.S)
    if match:
        return strip_tags(match.group(1))
    text = strip_tags(html)
    return text[:280]


def count_internal_links(html: str) -> int:
    hrefs = re.findall(r"""href=["']([^"'#]+)""", html or "", re.I)
    origin = site_origin()
    n = 0
    for href in hrefs:
        if href.startswith("/") and not href.startswith("//"):
            n += 1
        elif href.startswith(origin):
            n += 1
    return n


def images_missing_alt(html: str) -> int:
    missing = 0
    for tag in re.findall(r"<img\b[^>]*>", html or "", re.I):
        alt = re.search(r"""\balt\s*=\s*(['"])(.*?)\1""", tag, re.I)
        if not alt or not alt.group(2).strip():
            missing += 1
    return missing


def word_count(text: str) -> int:
    return len([w for w in strip_tags(text).split() if w])


def join_url(base: str, href: str) -> str:
    return urljoin(base, href)
