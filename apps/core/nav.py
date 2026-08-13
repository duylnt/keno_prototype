"""Public-site nav active-state. One item (or none) — never a perpetual highlight."""

from __future__ import annotations

from django.http import HttpRequest

LIVE_PREFIXES = (
    "/ket-qua-truc-tiep/",
    "/truc-tiep/",
    "/pos-display/",
    "/man-hinh-quay/",
)

INFO_PREFIXES = (
    "/thong-tin/",
    "/bai-viet/",
    "/huong-dan/",
    "/choi-thu/",
    "/trang/choi-co-trach-nhiem/",
    "/cong-dong/noi-quy/",
)


def normalize_path(path: str) -> str:
    path = (path or "/").split("?", 1)[0].split("#", 1)[0].strip() or "/"
    if not path.startswith("/"):
        path = "/" + path
    if path != "/" and not path.endswith("/"):
        path += "/"
    return path


def path_under(path: str, *prefixes: str) -> bool:
    """True when path is exactly a prefix or a child. `/` never matches everything."""
    path = normalize_path(path)
    for raw in prefixes:
        prefix = normalize_path(raw)
        if path == prefix:
            return True
        if prefix != "/" and path.startswith(prefix):
            return True
    return False


def nav_on(request: HttpRequest | str | None = None) -> dict[str, bool]:
    path = request.path if hasattr(request, "path") else (request or "/")
    live = path_under(path, *LIVE_PREFIXES)
    info_guidelines = path_under(path, "/cong-dong/noi-quy/")
    return {
        "live": live,
        "results": path_under(path, "/ket-qua/") and not live,
        "stats": path_under(path, "/thong-ke/"),
        "check": path_under(path, "/do-ve/"),
        "locations": path_under(path, "/diem-ban/")
        and not path_under(path, "/diem-ban/dang-nhap/"),
        "community": path_under(path, "/cong-dong/") and not info_guidelines,
        "info": path_under(path, *INFO_PREFIXES),
        "info_howto": path_under(path, "/huong-dan/"),
        "info_sim": path_under(path, "/choi-thu/"),
        "info_responsible": path_under(path, "/trang/choi-co-trach-nhiem/"),
        "info_guidelines": info_guidelines,
        "info_articles": path_under(path, "/bai-viet/"),
    }
