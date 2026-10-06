from rest_framework import permissions

from .models import EventMember


def membership_role(user, event):
    """Return 'owner', 'manager', 'scanner' or None for a user+event."""
    if not user.is_authenticated:
        return None
    if event.owner_id == user.id:
        return 'owner'
    member = event.members.filter(user=user).first()
    return member.role if member else None


class CanEditEvent(permissions.BasePermission):
    """Owner or manager may edit event/card/members; scanner cannot."""
    def has_object_permission(self, request, view, event):
        return membership_role(request.user, event) in ('owner', 'manager')


class IsEventStaff(permissions.BasePermission):
    """Owner, manager or scanner — door staff included."""
    def has_object_permission(self, request, view, event):
        return membership_role(request.user, event) is not None
