"""Check internal links on our own public pages. No third-party crawling."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.content.models import Article, StaticPage
from apps.locations.models import PosLocation

from .models import BrokenLink, SeoStatus
from .utils import normalize_path

HREF_RE = re.compile(r"""href=["']([^"'#]+)""", re.I)


def public_paths() -> list[str]:
    paths = [
        reverse("core:home"),
        reverse("results:live"),
        reverse("results:today"),
        reverse("results:history"),
        reverse("results:stats"),
        reverse("results:stats_size"),
        reverse("results:stats_parity"),
        reverse("results:check_ticket"),
        reverse("results:simulator"),
        reverse("locations:finder"),
        reverse("community:hub"),
        reverse("community:guidelines"),
        reverse("content:how_to_play"),
        reverse("content:info_hub"),
        reverse("content:article_list"),
    ]
    for article in Article.objects.filter(is_published=True, robots_noindex=False):
        paths.append(article.get_absolute_url())
    for page in StaticPage.objects.filter(is_published=True, robots_noindex=False):
        paths.append(page.get_absolute_url())
    for loc in PosLocation.objects.filter(is_active=True)[:40]:
        paths.append(loc.get_absolute_url())
    # unique
    seen, out = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _internal_targets(html: str, source: str) -> list[str]:
    found = []
    for href in HREF_RE.findall(html or ""):
        href = href.strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "data:")):
            continue
        parsed = urlparse(href)
        if parsed.scheme in {"http", "https"}:
            continue  # skip external
        if href.startswith("//"):
            continue
        path = parsed.path or href
        if not path.startswith("/"):
            path = normalize_path("/".join(source.rstrip("/").split("/")[:-1] + [path]))
        if path.startswith(("/static/", "/media/", "/cms/", "/api/")):
            continue
        found.append(path)
    return found


def check_internal_links() -> dict:
    client = Client()
    BrokenLink.objects.all().delete()
    ok = 0
    broken = 0
    checked_targets: dict[str, int] = {}
    for path in public_paths():
        resp = client.get(path, follow=True)
        if resp.status_code >= 400:
            BrokenLink.objects.create(
                source_path="(sitemap)",
                target_url=path,
                status_code=resp.status_code,
                is_internal=True,
            )
            broken += 1
            continue
        ok += 1
        html = resp.content.decode("utf-8", errors="replace")
        for target in _internal_targets(html, path):
            if target in checked_targets:
                code = checked_targets[target]
            else:
                t_resp = client.get(target, follow=False)
                code = t_resp.status_code
                if code in {301, 302} and t_resp.get("Location"):
                    loc = t_resp["Location"]
                    parsed = urlparse(loc)
                    follow_path = parsed.path or loc
                    followed = client.get(follow_path, follow=True)
                    code = followed.status_code
                checked_targets[target] = code
            if code >= 400 or code == 0:
                BrokenLink.objects.create(
                    source_path=path,
                    target_url=target,
                    status_code=code,
                    is_internal=True,
                )
                broken += 1
            else:
                ok += 1
    status = SeoStatus.load()
    status.linkcheck_at = timezone.now()
    status.linkcheck_ok = ok
    status.linkcheck_broken = BrokenLink.objects.count()
    status.save(update_fields=["linkcheck_at", "linkcheck_ok", "linkcheck_broken"])
    return {"ok": ok, "broken": status.linkcheck_broken, "checked_at": status.linkcheck_at}
