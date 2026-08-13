from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import display

from .models import (
    BannedKeyword,
    CommunityGuideline,
    CommunityPost,
    JoinQuestion,
    MinigameEvent,
)


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
