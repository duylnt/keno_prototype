from django.contrib.auth.models import Group

from .models import POS_OWNER_GROUP, PosLocation


def pos_owner_group() -> Group:
    group, _ = Group.objects.get_or_create(name=POS_OWNER_GROUP)
    return group


def is_pos_owner(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if user.groups.filter(name=POS_OWNER_GROUP).exists():
        return True
    return PosLocation.objects.filter(owner=user).exists()


def owned_locations(user):
    return PosLocation.objects.filter(owner=user).order_by("city", "name")
