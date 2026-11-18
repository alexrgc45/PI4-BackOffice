from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

from core.models import Utilizador


class UtilizadorJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError as exc:
            raise AuthenticationFailed("Token sem identificador de utilizador.") from exc

        try:
            return Utilizador.objects.get(pk=user_id, ativo=True)
        except Utilizador.DoesNotExist as exc:
            raise AuthenticationFailed("Utilizador inexistente ou inativo.") from exc
