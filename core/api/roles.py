from core.models import Administrador, Cliente, Colaborador, PermissaoColaborador


ADMINISTRATOR = "administrador"
COLLABORATOR = "colaborador"
CLIENT = "cliente"
RECECAO_TRABALHOS = "rececao_trabalhos"


def get_user_role(user):
    profile_checks = (
        (ADMINISTRATOR, Administrador.objects.filter(utilizador_id=user.pk).exists()),
        (COLLABORATOR, Colaborador.objects.filter(utilizador_id=user.pk).exists()),
        (CLIENT, Cliente.objects.filter(utilizador_id=user.pk).exists()),
    )
    roles = [role for role, exists in profile_checks if exists]
    return roles[0] if len(roles) == 1 else None


def get_user_permissions(user):
    role = get_user_role(user)
    if role == ADMINISTRATOR:
        return [
            code
            for code, _ in PermissaoColaborador.Codigo.choices
        ]
    if role != COLLABORATOR:
        return []

    return list(
        PermissaoColaborador.objects.filter(colaborador_id=user.pk)
        .order_by("codigo")
        .values_list("codigo", flat=True)
    )


def user_has_permission(user, permission_code):
    role = get_user_role(user)
    if role == ADMINISTRATOR:
        return True
    if role != COLLABORATOR:
        return False

    return PermissaoColaborador.objects.filter(
        colaborador_id=user.pk,
        codigo=permission_code,
    ).exists()
