from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Encomenda, PermissaoColaborador, Trabalho, Utilizador

from .roles import get_user_permissions, get_user_role


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
    perfil = serializers.SerializerMethodField()
    permissoes = serializers.SerializerMethodField()

    class Meta:
        model = Utilizador
        fields = ("id", "email", "ativo", "perfil", "permissoes")
        read_only_fields = fields

    def get_perfil(self, user):
        return get_user_role(user)

    def get_permissoes(self, user):
        return get_user_permissions(user)


class TrabalhoSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.CharField(source="encomenda.paciente_nome", read_only=True)
    tipo_trabalho_nome = serializers.CharField(source="tipo_trabalho.nome", read_only=True)

    class Meta:
        model = Trabalho
        fields = (
            "id",
            "encomenda",
            "paciente_nome",
            "tipo_trabalho_nome",
            "natureza",
            "estado",
            "data_limite",
            "data_proxima_consulta",
            "data_finalizacao",
        )
        read_only_fields = fields


class PermissaoColaboradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissaoColaborador
        fields = ("id", "codigo", "criada_em")
        read_only_fields = ("id", "criada_em")

    def create(self, validated_data):
        permission, _ = PermissaoColaborador.objects.get_or_create(
            colaborador=validated_data["colaborador"],
            codigo=validated_data["codigo"],
            defaults={"concedida_por": validated_data["concedida_por"]},
        )
        return permission


class EncomendaRececaoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source="cliente.nome", read_only=True)

    class Meta:
        model = Encomenda
        fields = (
            "id",
            "cliente",
            "cliente_nome",
            "paciente_nome",
            "paciente_idade",
            "paciente_sexo",
            "estado",
            "data_criacao",
        )
        read_only_fields = fields
