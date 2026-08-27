from rest_framework.permissions import BasePermission


class IsStoreOwner(BasePermission):
    message = "You must be the owner of this store."

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user