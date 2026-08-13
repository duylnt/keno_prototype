"""Keno Digital Ecosystem — Django settings."""

from pathlib import Path
import os

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-keno-prototype-secret-key")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [
    h.strip()
    for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]
if DEBUG:
    for host in ("localhost", "127.0.0.1", "testserver"):
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in env(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if o.strip()
]

SITE_URL = env("SITE_URL", "http://127.0.0.1:8000").rstrip("/")
GA4_MEASUREMENT_ID = env("GA4_MEASUREMENT_ID")
GTM_CONTAINER_ID = env("GTM_CONTAINER_ID")
GA4_PROPERTY_ID = env("GA4_PROPERTY_ID")
GSC_SITE_URL = env("GSC_SITE_URL", "https://keno.example.com/")
GSC_CREDENTIALS_PATH = env("GSC_CREDENTIALS_PATH") or env("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_MAPS_API_KEY = env("GOOGLE_MAPS_API_KEY")
FACEBOOK_APP_ID = env("FACEBOOK_APP_ID")
FACEBOOK_PAGE_ID = env("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_URL = env("FACEBOOK_PAGE_URL")
FACEBOOK_PAGE_ACCESS_TOKEN = env("FACEBOOK_PAGE_ACCESS_TOKEN")
FACEBOOK_GROUP_URL = env("FACEBOOK_GROUP_URL")
FACEBOOK_COMMENTS_URL = env("FACEBOOK_COMMENTS_URL")
ZALO_GROUP_URL = env("ZALO_GROUP_URL")
OPENAI_API_KEY = env("OPENAI_API_KEY")
OPENAI_MODEL = env("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = env("ANTHROPIC_MODEL", "claude-sonnet-4-0")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "apps.core",
    "apps.results",
    "apps.content",
    "apps.community",
    "apps.locations",
    "apps.analytics",
    "apps.seo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.seo.middleware.SeoRedirectMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.analytics.middleware.SessionTrackingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_chrome",
                "apps.seo.context_processors.seo_defaults",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

UNFOLD = {
    "SITE_TITLE": "Keno CMS",
    "SITE_HEADER": _("Keno CMS"),
    "SITE_SUBHEADER": _("Nội dung · Cộng đồng · Báo cáo"),
    "SITE_URL": "/",
    "SITE_SYMBOL": "grid_view",
    "SITE_LOGO": {
        "light": lambda request: static("img/keno-logo.png"),
        "dark": lambda request: static("img/keno-logo.png"),
    },
    "SITE_ICON": {
        "light": lambda request: static("img/keno-icon.png"),
        "dark": lambda request: static("img/keno-icon.png"),
    },
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/png",
            "href": lambda request: static("img/keno-icon.png"),
        },
        {
            "rel": "icon",
            "sizes": "192x192",
            "type": "image/png",
            "href": lambda request: static("img/keno-icon.png"),
        },
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "THEME": "light",
    "STYLES": [
        lambda request: static("css/cms.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/cms-reports.js"),
    ],
    "BORDER_RADIUS": "8px",
    "COLORS": {
        "base": {
            "50": "#fafafa",
            "100": "#f4f4f5",
            "200": "#e4e4e7",
            "300": "#d4d4d8",
            "400": "#a1a1aa",
            "500": "#71717a",
            "600": "#52525b",
            "700": "#3f3f46",
            "800": "#27272a",
            "900": "#18181b",
            "950": "#09090b",
        },
        "primary": {
            "50": "#fef2f3",
            "100": "#fde6e8",
            "200": "#f9cfd4",
            "300": "#f3a8b0",
            "400": "#e97482",
            "500": "#d44558",
            "600": "#c41e3a",
            "700": "#a31832",
            "800": "#88172e",
            "900": "#74182c",
            "950": "#400811",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-700)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Tổng quan"),
                "separator": False,
                "items": [
                    {
                        "title": _("Trang chủ"),
                        "icon": "home",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Nội dung"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Bài viết SEO"),
                        "icon": "edit_note",
                        "link": reverse_lazy("admin:content_article_changelist"),
                    },
                    {
                        "title": _("Nhóm nội dung"),
                        "icon": "category",
                        "link": reverse_lazy("admin:content_articlecategory_changelist"),
                    },
                    {
                        "title": _("Trang tĩnh"),
                        "icon": "article",
                        "link": reverse_lazy("admin:content_staticpage_changelist"),
                    },
                    {
                        "title": _("Banner"),
                        "icon": "image",
                        "link": reverse_lazy("admin:core_banner_changelist"),
                    },
                ],
            },
            {
                "title": _("Công cụ SEO"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Tổng quan SEO"),
                        "icon": "troubleshoot",
                        "link": reverse_lazy("admin:seo_toolbox"),
                    },
                    {
                        "title": _("Phân tích URL"),
                        "icon": "link",
                        "link": reverse_lazy("admin:seo_research"),
                    },
                    {
                        "title": _("Viết bài AI"),
                        "icon": "auto_awesome",
                        "link": reverse_lazy("admin:seo_writer"),
                    },
                    {
                        "title": _("Redirect 301"),
                        "icon": "alt_route",
                        "link": reverse_lazy("admin:seo_seoredirect_changelist"),
                    },
                    {
                        "title": _("Nội dung thị trường"),
                        "icon": "public",
                        "link": reverse_lazy("admin:seo_researchurl_changelist"),
                    },
                    {
                        "title": _("Link hỏng"),
                        "icon": "link_off",
                        "link": reverse_lazy("admin:seo_brokenlink_changelist"),
                    },
                ],
            },
            {
                "title": _("Cộng đồng"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Bài thảo luận"),
                        "icon": "forum",
                        "link": reverse_lazy("admin:community_communitypost_changelist"),
                        "badge": "apps.analytics.nav.pending_posts_badge",
                        "badge_variant": "warning",
                    },
                    {
                        "title": _("Kiểm duyệt Fanpage"),
                        "icon": "campaign",
                        "link": reverse_lazy("admin:community_fanpage"),
                    },
                    {
                        "title": _("Bài Fanpage (cache)"),
                        "icon": "rss_feed",
                        "link": reverse_lazy("admin:community_facebookpagepost_changelist"),
                    },
                    {
                        "title": _("Nội quy"),
                        "icon": "gavel",
                        "link": reverse_lazy("admin:community_communityguideline_changelist"),
                    },
                    {
                        "title": _("Câu hỏi lọc"),
                        "icon": "quiz",
                        "link": reverse_lazy("admin:community_joinquestion_changelist"),
                    },
                    {
                        "title": _("Từ khóa cấm"),
                        "icon": "block",
                        "link": reverse_lazy("admin:community_bannedkeyword_changelist"),
                    },
                    {
                        "title": _("Minigame"),
                        "icon": "sports_esports",
                        "link": reverse_lazy("admin:community_minigameevent_changelist"),
                    },
                    {
                        "title": _("KPI nhóm"),
                        "icon": "group_add",
                        "link": reverse_lazy("admin:analytics_communitykpisnapshot_changelist"),
                    },
                ],
            },
            {
                "title": _("Kết quả"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Kỳ quay"),
                        "icon": "schedule",
                        "link": reverse_lazy("admin:results_draw_changelist"),
                    },
                ],
            },
            {
                "title": _("Điểm bán"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Điểm bán Keno"),
                        "icon": "storefront",
                        "link": reverse_lazy("admin:locations_poslocation_changelist"),
                    },
                    {
                        "title": _("Mã O2O"),
                        "icon": "qr_code_2",
                        "link": reverse_lazy("admin:locations_experiencecode_changelist"),
                    },
                    {
                        "title": _("Hoa hồng O2O"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:locations_commissionledger_changelist"),
                    },
                    {
                        "title": _("Yêu cầu quy đổi"),
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:locations_payoutrequest_changelist"),
                        "badge": "apps.analytics.nav.pending_payouts_badge",
                        "badge_variant": "warning",
                    },
                ],
            },
            {
                "title": _("Báo cáo"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Phễu tăng trưởng"),
                        "icon": "filter_alt",
                        "link": reverse_lazy("admin:report_funnel"),
                    },
                    {
                        "title": _("KPI Website"),
                        "icon": "language",
                        "link": reverse_lazy("admin:report_website"),
                    },
                    {
                        "title": _("Search Console"),
                        "icon": "travel_explore",
                        "link": reverse_lazy("admin:report_seo"),
                    },
                    {
                        "title": _("KPI Cộng đồng"),
                        "icon": "groups",
                        "link": reverse_lazy("admin:report_community"),
                    },
                    {
                        "title": _("Ý định O2O"),
                        "icon": "near_me",
                        "link": reverse_lazy("admin:report_o2o"),
                    },
                ],
            },
            {
                "title": _("Cài đặt"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Cài đặt website"),
                        "icon": "tune",
                        "link": reverse_lazy("admin:core_sitesettings_changelist"),
                    },
                    {
                        "title": _("KPI kỹ thuật"),
                        "icon": "speed",
                        "link": reverse_lazy("admin:analytics_technicalkpisnapshot_changelist"),
                    },
                    {
                        "title": _("Sự kiện nội bộ"),
                        "icon": "ads_click",
                        "link": reverse_lazy("admin:analytics_analyticsevent_changelist"),
                    },
                    {
                        "title": _("Snapshot GA4"),
                        "icon": "insights",
                        "link": reverse_lazy("admin:analytics_ga4snapshot_changelist"),
                    },
                    {
                        "title": _("Snapshot GSC"),
                        "icon": "query_stats",
                        "link": reverse_lazy("admin:analytics_gscsnapshot_changelist"),
                    },
                    {
                        "title": _("Từ khóa GSC"),
                        "icon": "search",
                        "link": reverse_lazy("admin:analytics_gscquery_changelist"),
                    },
                    {
                        "title": _("KPI hàng ngày"),
                        "icon": "table_chart",
                        "link": reverse_lazy("admin:analytics_dailymetric_changelist"),
                    },
                ],
            },
        ],
    },
    "DASHBOARD_CALLBACK": "apps.core.dashboard.dashboard_callback",
}
