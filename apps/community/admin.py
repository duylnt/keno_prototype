from django.contrib import admin
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import display

from .models import (
    BannedKeyword,
    CommunityGuideline,
    CommunityPost,
    FacebookPagePost,
    JoinQuestion,
    MinigameEvent,
)
from .views_admin import FanpageModeratePostView, FanpageModerationView, FanpageSyncView


@admin.register(CommunityGuideline)
class CommunityGuidelineAdmin(ModelAdmin):
    list_display = ("title", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")


@admin.register(JoinQuestion)
class JoinQuestionAdmin(ModelAdmin):
    list_display = ("question", "sort_order", "is_active")
    list_editable = ("sort_order",)


@admin.register(BannedKeyword)
class BannedKeywordAdmin(ModelAdmin):
    list_display = ("keyword", "reason", "is_active")
    search_fields = ("keyword",)


@admin.register(CommunityPost)
class CommunityPostAdmin(ModelAdmin):
    list_display = (
        "title",
        "author_name",
        "pillar",
        "status_badge",
        "is_featured",
        "comment_count",
        "created_at",
    )
    list_filter = ("status", "pillar", "is_featured", ("created_at", RangeDateFilter))
    search_fields = ("title", "body", "author_name")
    list_editable = ("is_featured",)
    actions = ("approve_selected", "reject_spam")

    @display(
        description=_("Trạng thái"),
        label={
            CommunityPost.STATUS_APPROVED: "success",
            CommunityPost.STATUS_PENDING: "warning",
            CommunityPost.STATUS_REJECTED: "danger",
        },
    )
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()

    @admin.action(description=_("Duyệt bài"))
    def approve_selected(self, request, queryset):
        queryset.update(status=CommunityPost.STATUS_APPROVED, moderated_at=timezone.now())

    @admin.action(description=_("Từ chối (spam / bán số)"))
    def reject_spam(self, request, queryset):
        queryset.update(
            status=CommunityPost.STATUS_REJECTED,
            rejection_reason="Spam / nội dung không phù hợp",
            moderated_at=timezone.now(),
        )


@admin.register(MinigameEvent)
class MinigameEventAdmin(ModelAdmin):
    list_display = ("title", "scheduled_at", "participants", "is_published")
    list_filter = ("is_published",)


@admin.register(FacebookPagePost)
class FacebookPagePostAdmin(ModelAdmin):
    list_display = ("short_message", "created_time", "is_published", "is_hidden", "synced_at")
    list_filter = ("is_published", "is_hidden")
    search_fields = ("fb_id", "message")
    readonly_fields = ("fb_id", "message", "created_time", "permalink", "synced_at", "last_api_error")

    @display(description=_("Nội dung"))
    def short_message(self, obj):
        return str(obj)

    def has_add_permission(self, request):
        return False


def _register_fanpage_admin_urls():
    original = admin.site.get_urls

    def get_urls():
        extra = [
            path(
                "cong-dong/fanpage/",
                admin.site.admin_view(FanpageModerationView.as_view()),
                name="community_fanpage",
            ),
            path(
                "cong-dong/fanpage/dong-bo/",
                admin.site.admin_view(FanpageSyncView.as_view()),
                name="community_fanpage_sync",
            ),
            path(
                "cong-dong/fanpage/<int:pk>/xu-ly/",
                admin.site.admin_view(FanpageModeratePostView.as_view()),
                name="community_fanpage_moderate",
            ),
        ]
        return extra + original()

    admin.site.get_urls = get_urls


_register_fanpage_admin_urls()
