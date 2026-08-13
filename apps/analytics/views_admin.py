from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from .google import sync_ga4, sync_gsc
from .reports import build_kpi_report

REPORT_PAGES = [
    {"key": "funnel", "title": "Phễu tăng trưởng", "url_name": "admin:report_funnel"},
    {"key": "website", "title": "KPI Website", "url_name": "admin:report_website"},
    {"key": "seo", "title": "Search Console", "url_name": "admin:report_seo"},
    {"key": "community", "title": "KPI Cộng đồng", "url_name": "admin:report_community"},
    {"key": "o2o", "title": "Ý định O2O", "url_name": "admin:report_o2o"},
]


class ReportView(TemplateView):
    report_key = "funnel"
    title = "Báo cáo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        report = build_kpi_report(self.request)
        context.update(report)
        context["title"] = self.title
        context["report_key"] = self.report_key
        context["report_pages"] = REPORT_PAGES
        context["ga4_configured"] = bool(settings.GA4_PROPERTY_ID and settings.GSC_CREDENTIALS_PATH)
        context["gsc_configured"] = bool(settings.GSC_SITE_URL and settings.GSC_CREDENTIALS_PATH)
        context["ga4_property"] = settings.GA4_PROPERTY_ID or "(chưa cấu hình)"
        context["gsc_site"] = settings.GSC_SITE_URL
        query = self.request.GET.urlencode()
        context["range_query"] = f"?{query}" if query else ""
        return context


class FunnelReportView(ReportView):
    template_name = "admin/reports/funnel.html"
    report_key = "funnel"
    title = "Phễu tăng trưởng"


class WebsiteReportView(ReportView):
    template_name = "admin/reports/website.html"
    report_key = "website"
    title = "KPI Website"


class SeoReportView(ReportView):
    template_name = "admin/reports/seo.html"
    report_key = "seo"
    title = "Search Console"


class CommunityReportView(ReportView):
    template_name = "admin/reports/community.html"
    report_key = "community"
    title = "KPI Cộng đồng"


class O2OReportView(ReportView):
    template_name = "admin/reports/o2o.html"
    report_key = "o2o"
    title = "Ý định O2O"


class AnalyticsDashboardView(FunnelReportView):
    """Backward-compatible alias for /cms/bao-cao-kpi/."""


class SyncGoogleView(View):
    def post(self, request):
        source = request.POST.get("source")
        nxt = request.POST.get("next") or reverse("admin:report_funnel")
        try:
            if source == "ga4":
                n = sync_ga4()
                messages.success(request, f"Đã đồng bộ {n} ngày từ GA4.")
            elif source == "gsc":
                d, q = sync_gsc()
                messages.success(request, f"Đã đồng bộ {d} ngày GSC và {q} từ khóa.")
            else:
                messages.error(request, "Nguồn không hợp lệ.")
        except Exception as exc:
            messages.error(request, f"Đồng bộ thất bại: {exc}")
        return redirect(nxt)
