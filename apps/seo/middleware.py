from django.db.models import F
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from .utils import normalize_path


class SeoRedirectMiddleware:
    """Apply CMS-managed 301/302 redirects for public paths."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith(("/cms", "/static", "/media", "/api")):
            return self.get_response(request)
        try:
            from .models import SeoRedirect
        except Exception:
            return self.get_response(request)

        candidates = [path, normalize_path(path)]
        obj = (
            SeoRedirect.objects.filter(is_active=True, from_path__in=candidates)
            .order_by("-is_permanent")
            .first()
        )
        if not obj:
            return self.get_response(request)
        target = obj.to_path
        if not target.startswith(("http://", "https://")):
            target = normalize_path(target)
        SeoRedirect.objects.filter(pk=obj.pk).update(hit_count=F("hit_count") + 1)
        if target.startswith("http"):
            if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
                return self.get_response(request)
        return redirect(target, permanent=obj.is_permanent)
