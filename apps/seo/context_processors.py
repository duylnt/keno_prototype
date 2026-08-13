from django.conf import settings

from .utils import absolute_url, canonical_for_request, site_origin


def seo_defaults(request):
    origin = site_origin()
    canonical = canonical_for_request(request)
    noindex_prefixes = ("/pos/quet-ma/", "/pos-display/", "/man-hinh-quay/", "/cms/")
    robots = "noindex,follow" if request.path.startswith(noindex_prefixes) else "index,follow"
    return {
        "canonical_url": canonical,
        "seo_og_type": "website",
        "seo_og_image": "",
        "seo_robots": robots,
        "seo_llms_url": absolute_url("/llms.txt"),
        "site_origin": origin,
        "ga4_measurement_setting": settings.GA4_MEASUREMENT_ID,
        "gtm_container_setting": settings.GTM_CONTAINER_ID,
    }
