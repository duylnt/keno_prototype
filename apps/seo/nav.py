from django.http import HttpRequest


def _path_is(request: HttpRequest, *fragments: str) -> bool:
    path = request.path.rstrip("/") + "/"
    return any(f"/cms/{frag}/" in path or path.endswith(f"/{frag}/") for frag in fragments)


def active_toolbox(request: HttpRequest) -> bool:
    return _path_is(request, "seo/cong-cu")


def active_research(request: HttpRequest) -> bool:
    return _path_is(request, "seo/phan-tich-url")


def active_writer(request: HttpRequest) -> bool:
    return _path_is(request, "seo/viet-bai")
