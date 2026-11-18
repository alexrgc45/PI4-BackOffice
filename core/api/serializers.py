from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Utilizador


class TokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        try:
            user = Utilizador.objects.get(email=attrs["email"])
        except Utilizador.DoesNotExist as exc:
            raise AuthenticationFailed("Credenciais inválidas.") from exc

        if not user.ativo or not check_password(attrs["password"], user.password_hash):
            raise AuthenticationFailed("Credenciais inválidas.")

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.pk,
                "email": user.email,
            },
        }


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilizador
        fields = ("id", "email", "ativo")
        read_only_fields = fields
