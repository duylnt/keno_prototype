from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.community.facebook import (
    MANAGE_PERMISSIONS,
    READ_PERMISSIONS,
    facebook_moderation_links,
    moderate_cached_post,
    probe_api_status,
    sync_facebook_page,
)
from apps.community.models import CommunityPost, FacebookPagePost
from apps.core.models import SiteSettings


class FanpageModerationView(TemplateView):
    template_name = "admin/community/fanpage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        site = SiteSettings.load()
        status = probe_api_status()
        context.update(
            {
                "title": "Kiểm duyệt Fanpage",
                "fb_status": status,
                "fb_links": facebook_moderation_links(),
                "fb_posts": FacebookPagePost.objects.all()[:40],
                "pending_local": CommunityPost.objects.filter(
                    status=CommunityPost.STATUS_PENDING
                ).count(),
                "read_perm": READ_PERMISSIONS,
                "manage_perm": MANAGE_PERMISSIONS,
                "moderation_notes": site.facebook_moderation_roles,
            }
        )
        return context


class FanpageSyncView(View):
    def post(self, request):
        result = sync_facebook_page()
        if result["ok"]:
            messages.success(
                request,
                f"Đã đồng bộ Fanpage: {result['created']} bài mới, {result['updated']} cập nhật.",
            )
        else:
            extra = f" Cần quyền {result['permission']}." if result.get("permission") else ""
            messages.error(request, f"{result['error']}{extra}")
        return redirect("admin:community_fanpage")


class FanpageModeratePostView(View):
    def post(self, request, pk):
        post = get_object_or_404(FacebookPagePost, pk=pk)
        action = (request.POST.get("action") or "").strip()
        result = moderate_cached_post(post, action)
        if result["ok"]:
            labels = {"hide": "Đã ẩn bài trên Page.", "unpublish": "Đã gỡ đăng.", "show": "Đã hiện lại."}
            messages.success(request, labels.get(action, "Đã gửi lên Graph API."))
        else:
            extra = f" Cần {result.get('permission') or MANAGE_PERMISSIONS}." if result.get("permission") else ""
            messages.error(request, f"Không thực hiện được trên Facebook. {result['error']}{extra}")
        return redirect("admin:community_fanpage")
