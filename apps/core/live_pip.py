"""Picture-in-picture state for the live Keno draw.

Close / Tắt hides the floating player until the user opens Trực tiếp again.
A new kỳ does not reopen it on its own.
"""

WATCH_COOKIE = "keno_live_pip"
OFF_COOKIE = "keno_live_pip_off"


def pip_flags(request, *, on_live: bool, period: str = "") -> dict:
    watching = request.COOKIES.get(WATCH_COOKIE) == "1"
    dismissed = bool(request.COOKIES.get(OFF_COOKIE))
    return {
        "watching": watching,
        "dismissed": dismissed,
        "on_live": on_live,
        "visible": watching and not dismissed and not on_live,
        "period": period or "",
    }


def arm_watching(response):
    """Mark this browser as watching live; visiting Trực tiếp re-enables PiP."""
    response.set_cookie(WATCH_COOKIE, "1", samesite="Lax", path="/")
    response.delete_cookie(OFF_COOKIE, path="/")
    return response
