from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import (
    Cliente,
    Colaborador,
    Encomenda,
    EtapaTrabalho,
    Material,
    MedicoResponsavel,
    Notificacao,
    PermissaoColaborador,
    TemplateEtapa,
    Trabalho,
    TrabalhoDente,
    TrabalhoMaterial,
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


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs["refresh"])
        except TokenError as exc:
            raise AuthenticationFailed(
                "O token de sessão é inválido ou expirou."
            ) from exc

        issued_at = refresh.payload.get("iat")
        max_age = api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()
        if not isinstance(issued_at, int) or (
            timezone.now().timestamp() - issued_at >= max_age
        ):
            raise AuthenticationFailed("A sessão expirou.")

        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        if user_id is None:
            raise AuthenticationFailed(
                "O token de sessão não identifica um utilizador."
            )

        try:
            user = Utilizador.objects.get(
                **{api_settings.USER_ID_FIELD: user_id},
            )
        except Utilizador.DoesNotExist as exc:
            raise AuthenticationFailed("Utilizador inexistente.") from exc

        if not user.ativo:
            raise AuthenticationFailed("O utilizador está inativo.")

        return {"access": str(refresh.access_token)}


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
    medicos_responsaveis = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="nome",
    )

    class Meta:
        model = Cliente
        fields = (
            "id",
            "nome",
            "medicos_responsaveis",
            "nif",
            "email_contacto",
            "telefone",
            "tem_conta",
            "ativo",
        )
        read_only_fields = fields


class ClienteDetailSerializer(ClienteSerializer):
    email_contacto = serializers.SerializerMethodField()

    class Meta(ClienteSerializer.Meta):
        fields = ClienteSerializer.Meta.fields + ("morada",)
        read_only_fields = fields

    def get_email_contacto(self, client):
        if client.email_contacto:
            return client.email_contacto
        if client.utilizador_id:
            return client.utilizador.email
        return None


class MedicoResponsavelNamesField(serializers.ListField):
    def to_representation(self, value):
        if hasattr(value, "all"):
            value = value.all().values_list("nome", flat=True)
        return super().to_representation(value)


class AdminClienteCreateSerializer(serializers.ModelSerializer):
    nif = serializers.RegexField(
        regex=r"^[0-9]{9}$",
        min_length=9,
        max_length=9,
    )
    medicos_responsaveis = MedicoResponsavelNamesField(
        child=serializers.CharField(max_length=255),
        min_length=1,
    )
    email_contacto = serializers.EmailField(
        required=False,
        max_length=255,
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        min_length=8,
        max_length=128,
        required=False,
        allow_blank=True,
    )
    telefone = serializers.RegexField(
        regex=r"^[0-9]{9}$",
        required=False,
        allow_blank=True,
        allow_null=True,
        min_length=9,
        max_length=9,
    )
    morada = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    class Meta:
        model = Cliente
        fields = (
            "id",
            "nome",
            "medicos_responsaveis",
            "nif",
            "email_contacto",
            "password",
            "telefone",
            "morada",
        )
        read_only_fields = ("id",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is None:
            self.fields["email_contacto"].required = True
            self.fields["password"].required = True
            self.fields["password"].allow_blank = False

    def validate_nif(self, value):
        clients = Cliente.objects.filter(nif=value)
        if self.instance is not None:
            clients = clients.exclude(pk=self.instance.pk)
        if clients.exists():
            raise serializers.ValidationError(
                "Já existe um cliente com este NIF."
            )
        return value

    def validate_email_contacto(self, value):
        value = value.strip().lower()
        users = Utilizador.objects.filter(email__iexact=value)
        if self.instance is not None and self.instance.utilizador_id:
            users = users.exclude(pk=self.instance.utilizador_id)
        if users.exists():
            raise serializers.ValidationError(
                "Este e-mail já está associado a uma conta."
            )
        return value

    def validate(self, attrs):
        if self.instance is not None and not self.instance.utilizador_id:
            email = attrs.get("email_contacto", self.instance.email_contacto)
            password = attrs.get("password")
            errors = {}
            if not email:
                errors["email_contacto"] = (
                    "Indique um e-mail para criar a conta deste cliente."
                )
            if not password:
                errors["password"] = (
                    "Defina uma password para criar a conta deste cliente."
                )
            if errors:
                raise serializers.ValidationError(errors)
        return attrs

    def validate_medicos_responsaveis(self, names):
        normalized_names = [name.casefold() for name in names]
        if len(normalized_names) != len(set(normalized_names)):
            raise serializers.ValidationError(
                "Cada médico responsável só pode ser adicionado uma vez."
            )
        return names

    @transaction.atomic
    def create(self, validated_data):
        doctor_names = validated_data.pop("medicos_responsaveis")
        password = validated_data.pop("password")
        now = timezone.now()
        user = Utilizador.objects.create(
            email=validated_data["email_contacto"],
            password_hash=make_password(password),
            ativo=validated_data.get("ativo", True),
            criado_em=now,
            atualizado_em=now,
        )
        validated_data["utilizador"] = user
        validated_data["tem_conta"] = True
        client = super().create(validated_data)
        MedicoResponsavel.objects.bulk_create(
            [
                MedicoResponsavel(cliente=client, nome=name)
                for name in doctor_names
            ]
        )
        return client

    @transaction.atomic
    def update(self, instance, validated_data):
        doctor_names = validated_data.pop("medicos_responsaveis", None)
        password = validated_data.pop("password", "")
        email_was_submitted = "email_contacto" in validated_data
        client = super().update(instance, validated_data)
        if not client.utilizador_id:
            now = timezone.now()
            client.utilizador = Utilizador.objects.create(
                email=client.email_contacto,
                password_hash=make_password(password),
                ativo=client.ativo,
                criado_em=now,
                atualizado_em=now,
            )
            client.tem_conta = True
            client.save(update_fields=("utilizador", "tem_conta"))
        else:
            user = client.utilizador
            user_fields = []
            if email_was_submitted and user.email != client.email_contacto:
                user.email = client.email_contacto
                user_fields.append("email")
            if password:
                user.password_hash = make_password(password)
                user_fields.append("password_hash")
            if user_fields:
                user.atualizado_em = timezone.now()
                user_fields.append("atualizado_em")
                user.save(update_fields=user_fields)
        if doctor_names is not None:
            instance.medicos_responsaveis.all().delete()
            MedicoResponsavel.objects.bulk_create(
                [
                    MedicoResponsavel(cliente=instance, nome=name)
                    for name in doctor_names
                ]
            )
        return client


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


class AdminColaboradorUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="utilizador.email", max_length=255)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        min_length=8,
        max_length=128,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Colaborador
        fields = ("nome", "email", "password")

    def validate_email(self, value):
        value = value.strip().lower()
        users = Utilizador.objects.filter(email__iexact=value).exclude(
            pk=self.instance.utilizador_id
        )
        if users.exists():
            raise serializers.ValidationError(
                "Este e-mail já está associado a outra conta."
            )
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop("utilizador", {})
        email = user_data.get("email")
        password = validated_data.pop("password", "")
        collaborator = super().update(instance, validated_data)
        user = collaborator.utilizador
        user_fields = []

        if email is not None and user.email != email:
            user.email = email
            user_fields.append("email")
        if password:
            user.password_hash = make_password(password)
            user_fields.append("password_hash")
        if user_fields:
            user.atualizado_em = timezone.now()
            user_fields.append("atualizado_em")
            user.save(update_fields=user_fields)

        return collaborator


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


class AdminWorkCreateSerializer(serializers.Serializer):
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.filter(ativo=True)
    )
    paciente_nome = serializers.CharField(max_length=255, trim_whitespace=True)
    tipo_trabalho = serializers.PrimaryKeyRelatedField(
        queryset=TipoTrabalho.objects.filter(ativo=True)
    )
    materiais = serializers.ListField(
        child=serializers.CharField(max_length=150, trim_whitespace=True),
        required=False,
        allow_empty=True,
        max_length=20,
    )
    dentes = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        max_length=32,
    )
    data_limite = serializers.DateField(required=False, allow_null=True)
    observacoes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
        trim_whitespace=True,
    )
    ficheiros = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False),
        required=False,
        allow_empty=True,
        max_length=5,
    )

    valid_teeth = frozenset(
        (
            11, 12, 13, 14, 15, 16, 17, 18,
            21, 22, 23, 24, 25, 26, 27, 28,
            31, 32, 33, 34, 35, 36, 37, 38,
            41, 42, 43, 44, 45, 46, 47, 48,
        )
    )

    def validate_paciente_nome(self, value):
        if not value:
            raise serializers.ValidationError("Indica o nome do paciente.")
        return value

    def validate_materiais(self, value):
        if any(not material for material in value):
            raise serializers.ValidationError("Indica nomes de materiais válidos.")

        unique_materials = []
        seen = set()
        for material in value:
            normalized = material.casefold()
            if normalized not in seen:
                unique_materials.append(material)
                seen.add(normalized)
        return unique_materials

    def validate_ficheiros(self, value):
        max_file_size = 25 * 1024 * 1024
        max_total_size = 50 * 1024 * 1024
        if any(upload.size > max_file_size for upload in value):
            raise serializers.ValidationError(
                "Cada ficheiro pode ter no máximo 25 MB."
            )
        if sum(upload.size for upload in value) > max_total_size:
            raise serializers.ValidationError(
                "O tamanho total dos ficheiros não pode exceder 50 MB."
            )
        return value

    def validate_dentes(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Cada dente só pode ser selecionado uma vez.")
        invalid_teeth = sorted(set(value) - self.valid_teeth)
        if invalid_teeth:
            raise serializers.ValidationError(
                f"Número de dente inválido: {', '.join(map(str, invalid_teeth))}."
            )
        return value

    def create(self, validated_data):
        client = validated_data["cliente"]
        work_type = validated_data["tipo_trabalho"]
        materials = validated_data.pop("materiais", [])
        teeth = validated_data.pop("dentes", [])
        created_by = validated_data.pop("criada_por")
        patient_name = validated_data.pop("paciente_nome")
        due_date = validated_data.pop("data_limite", None)
        notes = validated_data.pop("observacoes", "")
        now = timezone.now()

        order = Encomenda.objects.create(
            cliente=client,
            criada_por=created_by,
            paciente_nome=patient_name,
            estado="Aceite",
            data_criacao=now,
        )
        work = Trabalho.objects.create(
            encomenda=order,
            tipo_trabalho=work_type,
            natureza="Prótese dentária",
            estado="Por Iniciar",
            data_limite=due_date,
            observacoes=notes,
            criado_em=now,
            atualizado_em=now,
        )

        for material_name in materials:
            material, _ = Material.objects.get_or_create(
                nome=material_name,
                defaults={"ativo": True},
            )
            if not material.ativo:
                raise serializers.ValidationError(
                    {"materiais": f'O material "{material_name}" está inativo.'}
                )
            TrabalhoMaterial.objects.create(
                trabalho=work,
                material=material,
                observacoes="",
            )

        for tooth_number in teeth:
            TrabalhoDente.objects.create(
                trabalho=work,
                numero_dente=tooth_number,
            )

        templates = TemplateEtapa.objects.select_for_update().filter(
            tipo_trabalho=work_type,
            ativa=True,
        ).order_by("ordem", "pk")
        for template in templates:
            EtapaTrabalho.objects.create(
                trabalho=work,
                template_etapa=template,
                nome=template.nome_etapa,
                ordem=template.ordem,
                estado="Por Iniciar",
                ativa=True,
                criada_em=now,
                atualizada_em=now,
            )

        return work


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
