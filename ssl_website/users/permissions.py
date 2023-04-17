from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import UserRole


class ReadOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class AdminPermission(BasePermission):
    """Класс для разрешения доступа только администратору."""

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return (
                request.user.role == UserRole.ADMIN
                or request.user.is_staff
                or request.user.is_superuser
            )

    def has_object_permission(self, request, view, obj):
        print(request.user.role)
        return request.method in SAFE_METHODS or (
            request.user.role == UserRole.ADMIN
            or request.user.is_staff
            or request.user.is_superuser
        )


class StudentPermission(BasePermission):
    """Класс для разрешения доступа только студенту."""
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            # print(request.user.role == UserRole.STUDENT)
            return request.user.role == UserRole.STUDENT


class ArbitratorPermission(BasePermission):
    """Класс для разрешения доступа только арбитру."""
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.role == UserRole.ARBITRATOR

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (
                request.user.role == UserRole.ARBITRATOR
        )