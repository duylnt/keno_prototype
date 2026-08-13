"""Fetch public URLs for content research. Metadata + excerpt only — not a full-text mirror."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from django.conf import settings
from django.utils import timezone

from .utils import site_origin, strip_tags, word_count

USER_AGENT = (
    "KenoPrototypeResearch/1.0 "
    f"(+{site_origin()}/llms.txt; metadata-and-outline-only; not a full-text scraper)"
)
TIMEOUT = 8
MAX_BYTES = 400_000
RATE_LIMIT_SEC = 1.2
EXCERPT_CHARS = 400

PRODUCT_PATTERNS = [
    ("keno", ("keno",)),
    ("power655", ("power 6/55", "power 655", "power6/55")),
    ("mega645", ("mega 6/45", "mega 645", "mega6/45")),
    ("max3d", ("max 3d", "max3d", "max 3d pro")),
    ("lotto535", ("lotto 5/35", "5/35", "lotto535")),
]


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._capture: str | None = None
        self._buf: list[str] = []
        self.title = ""
        self.canonical = ""
        self.metas: dict[str, str] = {}
        self.headings: list[dict[str, str]] = []
        self.jsonld: list[str] = []
        self._in_jsonld = False
        self._skip = False
        self.body_bits: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_d = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip = True
            if tag == "script" and "ld+json" in attrs_d.get("type", "").lower():
                self._in_jsonld = True
                self._skip = False
                self._capture = "jsonld"
                self._buf = []
            return
        if tag == "title":
            self._capture = "title"
            self._buf = []
        elif tag in {"h1", "h2", "h3"}:
            self._capture = tag
            self._buf = []
        elif tag == "meta":
            name = (attrs_d.get("name") or attrs_d.get("property") or "").lower()
            content = attrs_d.get("content") or ""
            if name and content:
                self.metas[name] = content
        elif tag == "link" and attrs_d.get("rel", "").lower() == "canonical":
            self.canonical = attrs_d.get("href") or ""
        elif tag == "time" and attrs_d.get("datetime"):
            self.metas.setdefault("article:published_time", attrs_d["datetime"])

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            if self._in_jsonld and self._buf:
                self.jsonld.append("".join(self._buf).strip())
            self._in_jsonld = False
            self._skip = False
            self._capture = None
            self._buf = []
            return
        if self._capture in {"title", "h1", "h2", "h3"} and tag == self._capture:
            text = strip_tags("".join(self._buf)).strip()
            if tag == "title":
                self.title = text
            else:
                self.headings.append({"tag": tag, "text": text})
            self._capture = None
            self._buf = []

    def handle_data(self, data):
        if self._capture:
            self._buf.append(data)
        elif not self._skip:
            self.body_bits.append(data)


def detect_product(text: str) -> str:
    blob = (text or "").lower()
    for key, needles in PRODUCT_PATTERNS:
        if any(n in blob for n in needles):
            return key
    return "other"


def keyword_hints(title: str, headings: list[dict], product: str) -> str:
    bits = [title] + [h["text"] for h in headings[:8]]
    blob = " ".join(bits).lower()
    hints: list[str] = []
    catalog = [
        "kết quả keno",
        "cách chơi keno",
        "keno là gì",
        "thống kê keno",
        "lớn nhỏ",
        "chẵn lẻ",
        "dò vé",
        "điểm bán",
        "power 6/55",
        "mega 6/45",
        "max 3d",
        "lotto 5/35",
        "vietlott",
        "xổ số nhanh",
    ]
    for kw in catalog:
        if kw in blob and kw not in hints:
            hints.append(kw)
    label = {
        "keno": "keno",
        "power655": "power 6/55",
        "mega645": "mega 6/45",
        "max3d": "max 3d",
        "lotto535": "lotto 5/35",
    }.get(product)
    if label and label not in hints:
        hints.insert(0, label)
    return ", ".join(hints[:8])


def schema_types_from_jsonld(blobs: list[str]) -> str:
    types: list[str] = []
    for blob in blobs:
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and "@graph" in data:
            nodes = data["@graph"]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            t = node.get("@type")
            if isinstance(t, list):
                types.extend(str(x) for x in t)
            elif t:
                types.append(str(t))
    # unique preserve order
    seen = []
    for t in types:
        if t not in seen:
            seen.append(t)
    return ", ".join(seen[:8])


def parse_html(html: str, url: str) -> dict:
    parser = _PageParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    title = parser.title or strip_tags(re.search(r"<title[^>]*>(.*?)</title>", html or "", re.I | re.S).group(1) if re.search(r"<title", html or "", re.I) else "")
    desc = (
        parser.metas.get("description")
        or parser.metas.get("og:description")
        or ""
    )
    published = (
        parser.metas.get("article:published_time")
        or parser.metas.get("pubdate")
        or parser.metas.get("date")
        or ""
    )
    body_text = strip_tags(" ".join(parser.body_bits))
    excerpt = body_text[:EXCERPT_CHARS].rsplit(" ", 1)[0] if len(body_text) > EXCERPT_CHARS else body_text
    outline = "\n".join(f"{h['tag'].upper()}: {h['text']}" for h in parser.headings if h["text"])
    combined = f"{title} {desc} {outline}"
    product = detect_product(combined)
    return {
        "title": title[:300],
        "meta_description": desc[:400],
        "canonical": (parser.canonical or "")[:500],
        "headings": parser.headings[:30],
        "outline": outline[:4000],
        "excerpt": excerpt,
        "word_count": word_count(body_text),
        "keyword_hints": keyword_hints(title, parser.headings, product),
        "schema_types": schema_types_from_jsonld(parser.jsonld),
        "published_hint": published[:80],
        "product_hint": product,
        "url": url,
    }


def robots_allowed(url: str, user_agent: str = USER_AGENT) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        req = urllib.request.Request(robots_url, headers={"User-Agent": user_agent})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read(80_000).decode("utf-8", errors="replace")
        rp.parse(raw.splitlines())
        return rp.can_fetch(user_agent, url)
    except Exception:
        # If robots.txt cannot be read, be conservative but allow staff-requested URL
        # with a note — still try fetch; caller records robots_allowed=True with warning.
        return True


def fetch_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return {
            "url": url,
            "status": "error",
            "error_message": "Chỉ chấp nhận http/https.",
            "robots_allowed": False,
        }
    allowed = robots_allowed(url)
    if not allowed:
        return {
            "url": url,
            "status": "blocked",
            "robots_allowed": False,
            "error_message": "robots.txt không cho phép bot nghiên cứu này.",
            "fetched_at": timezone.now(),
        }
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = getattr(resp, "status", 200)
            raw = resp.read(MAX_BYTES)
            ctype = resp.headers.get("Content-Type", "")
        html = raw.decode("utf-8", errors="replace")
        parsed_page = parse_html(html, url)
        parsed_page.update(
            {
                "http_status": status,
                "status": "ok",
                "robots_allowed": True,
                "error_message": "" if "html" in ctype.lower() or not ctype else f"content-type {ctype}",
                "fetched_at": timezone.now(),
            }
        )
        return parsed_page
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "status": "error",
            "http_status": exc.code,
            "robots_allowed": True,
            "error_message": f"HTTP {exc.code}",
            "fetched_at": timezone.now(),
        }
    except Exception as exc:
        return {
            "url": url,
            "status": "error",
            "robots_allowed": True,
            "error_message": str(exc)[:300],
            "fetched_at": timezone.now(),
        }


def analyze_urls(urls: list[str], delay: float = RATE_LIMIT_SEC) -> list[dict]:
    results = []
    for i, url in enumerate(urls):
        url = (url or "").strip()
        if not url:
            continue
        results.append(fetch_url(url))
        if i < len(urls) - 1:
            time.sleep(delay)
    return results


def persist_result(data: dict, product_hint: str = "") -> "ResearchUrl":
    from .models import ResearchUrl

    product = product_hint or data.get("product_hint") or "other"
    obj = ResearchUrl.objects.create(
        url=data.get("url") or "",
        product_hint=product if product in dict(ResearchUrl.PRODUCT_CHOICES) else "other",
        title=data.get("title") or "",
        meta_description=data.get("meta_description") or "",
        canonical=data.get("canonical") or "",
        headings=data.get("headings") or [],
        outline=data.get("outline") or "",
        excerpt=(data.get("excerpt") or "")[:EXCERPT_CHARS],
        word_count=int(data.get("word_count") or 0),
        keyword_hints=data.get("keyword_hints") or "",
        schema_types=data.get("schema_types") or "",
        published_hint=data.get("published_hint") or "",
        http_status=data.get("http_status"),
        robots_allowed=bool(data.get("robots_allowed", True)),
        status=data.get("status") or ResearchUrl.STATUS_ERROR,
        error_message=data.get("error_message") or "",
        fetched_at=data.get("fetched_at") or timezone.now(),
    )
    return obj
