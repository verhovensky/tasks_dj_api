from rest_framework import permissions


class IsActiveUser(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ только активным пользователям.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active


class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее только создателю объекта редактировать или удалять его.
    Остальные пользователи имеют только доступ на чтение.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешения на чтение доступны для любого запроса
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешения на запись только для создателя объекта
        return obj.created_by == request.user
