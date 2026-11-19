from django.contrib.auth.hashers import check_password
from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import (
    Cliente,
    Colaborador,
    Encomenda,
    Notificacao,
    PermissaoColaborador,
    TemplateEtapa,
    Trabalho,
    TipoTrabalho,
    Utilizador,
)

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


class AdminProfileSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    email = serializers.EmailField(source="utilizador.email")
    ativo = serializers.BooleanField(source="utilizador.ativo", read_only=True)

    def validate(self, attrs):
        email = attrs.get("utilizador", {}).get("email")
        if email is None:
            return attrs
        user = self.context["request"].user
        if Utilizador.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                {"detail": "Este e-mail já está associado a outra conta."}
            )
        return attrs

    def update(self, instance, validated_data):
        user_data = validated_data.pop("utilizador", {})
        profile_fields = []
        if "nome" in validated_data:
            instance.nome = validated_data["nome"]
            profile_fields.append("nome")
        if profile_fields:
            instance.save(update_fields=profile_fields)

        if user_data:
            user = instance.utilizador
            user.email = user_data["email"]
            user.atualizado_em = timezone.now()
            user.save(update_fields=("email", "atualizado_em"))
        elif profile_fields:
            user = instance.utilizador
            user.atualizado_em = timezone.now()
            user.save(update_fields=("atualizado_em",))
        return instance


class AdminPasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )
    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )

    def validate(self, attrs):
        user = self.context["user"]
        if not check_password(attrs["current_password"], user.password_hash):
            raise serializers.ValidationError(
                {"detail": "A palavra-passe atual está incorreta."}
            )
        if len(attrs["new_password"]) < 8:
            raise serializers.ValidationError(
                {"detail": "A nova palavra-passe deve ter pelo menos 8 caracteres."}
            )
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"detail": "A confirmação da palavra-passe não coincide."}
            )
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError(
                {"detail": "A nova palavra-passe deve ser diferente da atual."}
            )
        return attrs


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = (
            "id",
            "nome",
            "nif",
            "email_contacto",
            "telefone",
            "tem_conta",
            "ativo",
        )
        read_only_fields = fields


class ColaboradorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)
    email = serializers.EmailField(source="utilizador.email", read_only=True)
    permissoes = serializers.SerializerMethodField()

    class Meta:
        model = Colaborador
        fields = ("id", "nome", "email", "ativo", "permissoes")
        read_only_fields = fields

    def get_permissoes(self, collaborator):
        return [permission.codigo for permission in collaborator.permissoes.all()]


class UtilizadorPendenteSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()
    perfil = serializers.SerializerMethodField()

    class Meta:
        model = Utilizador
        fields = ("id", "email", "nome", "perfil", "criado_em")
        read_only_fields = fields

    def get_nome(self, user):
        client = getattr(user, "cliente", None)
        if client is not None:
            return client.nome
        return user.colaborador.nome

    def get_perfil(self, user):
        if getattr(user, "cliente", None) is not None:
            return "Cliente"
        return "Colaborador"


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = (
            "id",
            "tipo",
            "titulo",
            "conteudo",
            "trabalho",
            "criada_em",
            "lida_em",
        )
        read_only_fields = fields


class TipoTrabalhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTrabalho
        fields = ("id", "nome", "ativo")
        read_only_fields = fields


class TemplateEtapaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateEtapa
        fields = ("id", "tipo_trabalho", "nome_etapa", "ordem", "ativa")
        read_only_fields = ("id", "tipo_trabalho")
        extra_kwargs = {
            "nome_etapa": {"trim_whitespace": True},
            "ordem": {"min_value": 1},
        }

    def validate_ordem(self, value):
        if self.instance is not None:
            highest_order = TemplateEtapa.objects.filter(
                tipo_trabalho_id=self.instance.tipo_trabalho_id
            ).aggregate(highest_order=Max("ordem"))["highest_order"] or 0
            if value > highest_order:
                raise serializers.ValidationError(
                    f"A ordem não pode ser superior a {highest_order}."
                )
        return value


class TemplateEtapaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateEtapa
        fields = ("id", "tipo_trabalho", "nome_etapa", "ordem", "ativa")
        read_only_fields = ("id", "tipo_trabalho", "ordem", "ativa")
        extra_kwargs = {"nome_etapa": {"trim_whitespace": True}}


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
