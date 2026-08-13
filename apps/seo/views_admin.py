from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.content.models import ArticleCategory

from .crawler import analyze_urls, persist_result
from .links import check_internal_links
from .models import CoreWebVitalsNote, ResearchUrl, SeoStatus
from .overview import coverage_gaps, indexing_overview
from .sample_market import SAMPLE_MARKET
from .writer import api_configured, generate_article, save_draft


class SeoAdminMixin:
    title = "Công cụ SEO"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context["title"] = self.title
        context["seo_nav"] = [
            {"key": "toolbox", "title": "Tổng quan SEO", "url_name": "admin:seo_toolbox"},
            {"key": "research", "title": "Phân tích URL", "url_name": "admin:seo_research"},
            {"key": "writer", "title": "Viết bài AI", "url_name": "admin:seo_writer"},
        ]
        return context


class SeoToolboxView(SeoAdminMixin, TemplateView):
    template_name = "admin/seo/toolbox.html"
    title = "Công cụ SEO"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["overview"] = indexing_overview()
        context["seo_key"] = "toolbox"
        context["gaps"] = coverage_gaps()[:8]
        return context

    def post(self, request):
        action = request.POST.get("action")
        if action == "linkcheck":
            result = check_internal_links()
            messages.success(
                request,
                f"Đã kiểm tra link nội bộ: {result['ok']} ổn, {result['broken']} hỏng.",
            )
        elif action == "cwv":
            note, _ = CoreWebVitalsNote.objects.get_or_create(date=timezone.localdate())
            note.lcp_note = request.POST.get("lcp_note", "")[:200]
            note.inp_note = request.POST.get("inp_note", "")[:200]
            note.cls_note = request.POST.get("cls_note", "")[:200]
            note.notes = request.POST.get("cwv_notes", "")
            note.save()
            messages.success(request, "Đã lưu ghi chú Core Web Vitals.")
        return redirect("admin:seo_toolbox")


class SeoResearchView(SeoAdminMixin, TemplateView):
    template_name = "admin/seo/research.html"
    title = "Phân tích URL thị trường"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["seo_key"] = "research"
        context["rows"] = ResearchUrl.objects.all()[:80]
        context["gaps"] = coverage_gaps()
        context["seed_hint"] = "https://example.com/mau/keno-la-gi"
        return context

    def post(self, request):
        action = request.POST.get("action")
        if action == "samples":
            created = 0
            for row in SAMPLE_MARKET:
                if ResearchUrl.objects.filter(url=row["url"]).exists():
                    continue
                ResearchUrl.objects.create(
                    url=row["url"],
                    product_hint=row["product_hint"],
                    title=row["title"],
                    meta_description=row["meta_description"],
                    canonical=row["canonical"],
                    headings=row["headings"],
                    outline=row["outline"],
                    excerpt=row["excerpt"],
                    word_count=row["word_count"],
                    keyword_hints=row["keyword_hints"],
                    schema_types=row["schema_types"],
                    published_hint=row["published_hint"],
                    status=ResearchUrl.STATUS_SAMPLE,
                    robots_allowed=True,
                    fetched_at=timezone.now(),
                )
                created += 1
            SeoStatus.load()
            s = SeoStatus.load()
            s.research_at = timezone.now()
            s.save(update_fields=["research_at"])
            messages.success(request, f"Đã nạp {created} URL mẫu.")
            return redirect("admin:seo_research")

        raw = request.POST.get("urls") or ""
        product = request.POST.get("product_hint") or ""
        urls = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        if not urls:
            messages.error(request, "Dán ít nhất một URL.")
            return redirect("admin:seo_research")
        results = analyze_urls(urls)
        saved = 0
        blocked = 0
        errors = 0
        for data in results:
            persist_result(data, product_hint=product)
            saved += 1
            if data.get("status") == "blocked":
                blocked += 1
            elif data.get("status") == "error":
                errors += 1
        s = SeoStatus.load()
        s.research_at = timezone.now()
        s.save(update_fields=["research_at"])
        messages.success(
            request,
            f"Đã phân tích {saved} URL (chặn robots: {blocked}, lỗi: {errors}).",
        )
        return redirect("admin:seo_research")


class SeoWriterView(SeoAdminMixin, TemplateView):
    template_name = "admin/seo/writer.html"
    title = "Viết bài AI (bản nháp)"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["seo_key"] = "writer"
        context["api_configured"] = api_configured()
        context["categories"] = ArticleCategory.objects.all()
        context["topic"] = self.request.GET.get("topic", "")
        context["outline"] = self.request.GET.get("outline", "")
        context["research_notes"] = self.request.GET.get("notes", "")
        context["draft"] = None
        return context

    def post(self, request):
        topic = (request.POST.get("topic") or "").strip()
        outline = request.POST.get("outline") or ""
        notes = request.POST.get("research_notes") or ""
        category_id = request.POST.get("category")
        if not topic:
            messages.error(request, "Nhập chủ đề bài viết.")
            return redirect("admin:seo_writer")
        draft = generate_article(topic, outline, notes)
        if request.POST.get("save"):
            category = None
            if category_id:
                category = ArticleCategory.objects.filter(pk=category_id).first()
            article = save_draft(draft, category=category)
            messages.success(
                request,
                f"Đã lưu bản nháp «{article.title}» (chưa xuất bản, noindex). Hãy biên tập trước khi đăng.",
            )
            return redirect(reverse("admin:content_article_change", args=[article.pk]))
        context = self.get_context_data()
        context["draft"] = draft
        context["topic"] = topic
        context["outline"] = outline
        context["research_notes"] = notes
        context["selected_category"] = category_id
        return render(request, self.template_name, context)
