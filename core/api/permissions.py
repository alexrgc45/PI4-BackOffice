from rest_framework.permissions import BasePermission

from .roles import ADMINISTRATOR, get_user_role, user_has_permission


class HasLaboratoryProfile(BasePermission):
    message = "A conta não tem um perfil válido no laboratório."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and get_user_role(request.user)
        )


class IsAdministrator(BasePermission):
    message = "Esta ação só está disponível para administradores."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and get_user_role(request.user) == ADMINISTRATOR
        )


class HasDelegatedPermission(BasePermission):
    message = "Não tens permissão para aceder a esta área."

    def has_permission(self, request, view):
        permission_code = getattr(view, "permission_code", None)
        return bool(
            permission_code
            and request.user
            and request.user.is_authenticated
            and user_has_permission(request.user, permission_code)
        )
