import mimetypes
from pathlib import Path
from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import default_storage
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import F, Max, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    Administrador,
    Auditoria,
    Cliente,
    Colaborador,
    Convite,
    EtapaTrabalho,
    Encomenda,
    Ficheiro,
    Notificacao,
    PermissaoColaborador,
    RegistoUtilizador,
    TemplateEtapa,
    TentativaLogin,
    Trabalho,
    TipoTrabalho,
    Utilizador,
)

from .permissions import (
    HasDelegatedPermission,
    HasLaboratoryProfile,
    IsAdministrator,
)
from .roles import (
    ADMINISTRATOR,
    CLIENT,
    COLLABORATOR,
    RECECAO_TRABALHOS,
    get_user_role,
)
from .serializers import (
    AdminClienteCreateSerializer,
    AdminColaboradorUpdateSerializer,
    AdminPasswordChangeSerializer,
    AdminProfileSerializer,
    AdminWorkCreateSerializer,
    ClienteDetailSerializer,
    ClienteSerializer,
    ColaboradorSerializer,
    CurrentUserSerializer,
    EncomendaRececaoSerializer,
    PermissaoColaboradorSerializer,
    TokenObtainSerializer,
    TokenRefreshSerializer,
    TrabalhoSerializer,
    NotificacaoSerializer,
    UtilizadorPendenteSerializer,
    TemplateEtapaCreateSerializer,
    TemplateEtapaSerializer,
    TipoTrabalhoSerializer,
)


class TokenObtainView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = TokenObtainSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class TokenRefreshView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class CurrentUserView(APIView):
    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)


class AdminProfileView(APIView):
    permission_classes = (IsAdministrator,)

    def get_profile(self, user, lock=False):
        queryset = Administrador.objects.select_related("utilizador")
        if lock:
            queryset = queryset.select_for_update()
        return get_object_or_404(queryset, utilizador_id=user.pk)

    def get(self, request):
        profile = self.get_profile(request.user)
        return Response(
            AdminProfileSerializer(profile, context={"request": request}).data
        )

    def patch(self, request):
        try:
            with transaction.atomic():
                profile = self.get_profile(request.user, lock=True)
                serializer = AdminProfileSerializer(
                    profile,
                    data=request.data,
                    partial=True,
                    context={"request": request},
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "Este e-mail já está associado a outra conta."}
            ) from exc

        return Response(serializer.data)


class AdminPasswordChangeView(APIView):
    permission_classes = (IsAdministrator,)

    def post(self, request):
        with transaction.atomic():
            user = get_object_or_404(
                Utilizador.objects.select_for_update(),
                pk=request.user.pk,
                ativo=True,
            )
            serializer = AdminPasswordChangeSerializer(
                data=request.data,
                context={"user": user},
            )
            serializer.is_valid(raise_exception=True)
            user.password_hash = make_password(
                serializer.validated_data["new_password"]
            )
            user.atualizado_em = timezone.now()
            user.save(update_fields=("password_hash", "atualizado_em"))

        return Response({"detail": "Palavra-passe alterada com sucesso."})


class AdminWorkCreateView(APIView):
    permission_classes = (IsAdministrator,)

    def post(self, request):
        serializer = AdminWorkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_files = serializer.validated_data.pop("ficheiros", [])
        stored_keys = []
        file_records = []

        try:
            with transaction.atomic():
                client = get_object_or_404(
                    Cliente.objects.select_for_update(),
                    pk=serializer.validated_data["cliente"].pk,
                    ativo=True,
                )
                work_type = get_object_or_404(
                    TipoTrabalho.objects.select_for_update(),
                    pk=serializer.validated_data["tipo_trabalho"].pk,
                    ativo=True,
                )
                work = serializer.save(
                    cliente=client,
                    tipo_trabalho=work_type,
                    criada_por=request.user,
                )

                for uploaded_file in uploaded_files:
                    original_name = Path(
                        str(uploaded_file.name).replace("\\", "/")
                    ).name[:255]
                    storage_key = default_storage.save(
                        f"trabalhos/{work.pk}/{uuid4().hex}",
                        uploaded_file,
                    )
                    stored_keys.append(storage_key)
                    mime_type = (
                        mimetypes.guess_type(original_name)[0]
                        or "application/octet-stream"
                    )
                    file_records.append(
                        Ficheiro.objects.create(
                            trabalho=work,
                            enviado_por=request.user,
                            nome_original=original_name,
                            chave_armazenamento=storage_key,
                            tipo_mime=mime_type,
                            categoria="imagem" if mime_type.startswith("image/") else "outro",
                            tamanho_bytes=uploaded_file.size,
                            visivel_cliente=False,
                            enviado_em=timezone.now(),
                        )
                    )
        except (DatabaseError, OSError, SuspiciousFileOperation):
            for storage_key in stored_keys:
                default_storage.delete(storage_key)
            raise

        response_data = TrabalhoSerializer(work).data
        response_data["ficheiros"] = [
            {
                "id": file_record.pk,
                "nome_original": file_record.nome_original,
                "categoria": file_record.categoria,
                "tamanho_bytes": file_record.tamanho_bytes,
            }
            for file_record in file_records
        ]
        return Response(response_data, status=201)


class AdminWorkFileDownloadView(APIView):
    permission_classes = (IsAdministrator,)

    def get(self, request, pk):
        stored_file = get_object_or_404(Ficheiro, pk=pk)
        try:
            content = default_storage.open(stored_file.chave_armazenamento, "rb")
        except FileNotFoundError as exc:
            raise NotFound("O ficheiro anexado não está disponível.") from exc

        response = FileResponse(
            content,
            as_attachment=True,
            filename=stored_file.nome_original,
            content_type=stored_file.tipo_mime or "application/octet-stream",
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response


class ClienteListCreateView(generics.ListCreateAPIView):
    serializer_class = ClienteSerializer
    permission_classes = (IsAdministrator,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminClienteCreateSerializer
        return ClienteSerializer

    def get_queryset(self):
        return Cliente.objects.prefetch_related("medicos_responsaveis").order_by(
            "nome",
            "pk",
        )

    def perform_create(self, serializer):
        serializer.save(
            criado_por_admin=self.request.user,
            tem_conta=True,
            ativo=True,
        )


class ClienteDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAdministrator,)

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return AdminClienteCreateSerializer
        return ClienteDetailSerializer

    def get_queryset(self):
        return Cliente.objects.select_related("utilizador").prefetch_related(
            "medicos_responsaveis"
        )


class ColaboradorListView(generics.ListAPIView):
    serializer_class = ColaboradorSerializer
    permission_classes = (IsAdministrator,)

    def get_queryset(self):
        return Colaborador.objects.select_related("utilizador").prefetch_related(
            "permissoes"
        ).order_by("nome", "pk")


class ColaboradorDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAdministrator,)

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return AdminColaboradorUpdateSerializer
        return ColaboradorSerializer

    def get_queryset(self):
        return Colaborador.objects.select_related("utilizador").prefetch_related(
            "permissoes"
        )


class UtilizadorPendenteListView(generics.ListAPIView):
    serializer_class = UtilizadorPendenteSerializer
    permission_classes = (IsAdministrator,)

    def get_queryset(self):
        return (
            Utilizador.objects.filter(ativo=False)
            .filter(
                Q(
                    cliente__isnull=False,
                    cliente__ativo=False,
                    colaborador__isnull=True,
                )
                | Q(
                    cliente__isnull=True,
                    colaborador__isnull=False,
                    colaborador__ativo=False,
                )
            )
            .exclude(administrador__isnull=False)
            .select_related("cliente", "colaborador")
            .order_by("criado_em", "pk")
        )


def get_pending_user(pk):
    user = get_object_or_404(
        Utilizador.objects.select_for_update(),
        pk=pk,
        ativo=False,
    )
    if Administrador.objects.filter(utilizador_id=user.pk).exists():
        raise NotFound("A conta não está pendente de aprovação.")

    client = Cliente.objects.select_for_update().filter(
        utilizador_id=user.pk,
        ativo=False,
    ).first()
    collaborator = Colaborador.objects.select_for_update().filter(
        utilizador_id=user.pk,
        ativo=False,
    ).first()
    if (client is None) == (collaborator is None):
        raise NotFound("A conta não está pendente de aprovação.")
    if Cliente.objects.filter(utilizador_id=user.pk).exists() and client is None:
        raise NotFound("A conta não está pendente de aprovação.")
    if Colaborador.objects.filter(utilizador_id=user.pk).exists() and collaborator is None:
        raise NotFound("A conta não está pendente de aprovação.")
    return user, client or collaborator


class UtilizadorPendenteApproveView(APIView):
    permission_classes = (IsAdministrator,)

    def post(self, request, pk):
        with transaction.atomic():
            user, profile = get_pending_user(pk)
            profile.ativo = True
            profile.save(update_fields=("ativo",))
            user.ativo = True
            user.atualizado_em = timezone.now()
            user.save(update_fields=("ativo", "atualizado_em"))

        return Response({"detail": "Conta aprovada com sucesso."})


class UtilizadorPendenteRejectView(APIView):
    permission_classes = (IsAdministrator,)

    def delete(self, request, pk):
        try:
            with transaction.atomic():
                user, profile = get_pending_user(pk)
                RegistoUtilizador.objects.filter(utilizador=user).delete()
                TentativaLogin.objects.filter(utilizador=user).update(utilizador=None)
                Auditoria.objects.filter(utilizador=user).update(utilizador=None)
                Convite.objects.filter(utilizador_criado=user).update(
                    utilizador_criado=None
                )
                if isinstance(profile, Colaborador):
                    PermissaoColaborador.objects.filter(
                        colaborador=profile
                    ).delete()
                profile.delete()
                user.delete()
        except IntegrityError as exc:
            raise ValidationError(
                "A conta tem dados associados e não pode ser eliminada com segurança."
            ) from exc

        return Response(status=204)


class NotificacaoListView(generics.ListAPIView):
    serializer_class = NotificacaoSerializer
    permission_classes = (HasLaboratoryProfile,)

    def get_queryset(self):
        return Notificacao.objects.filter(
            utilizador_id=self.request.user.pk
        ).order_by("-criada_em", "-pk")


class NotificacaoMarkReadView(APIView):
    permission_classes = (HasLaboratoryProfile,)

    def post(self, request, pk):
        with transaction.atomic():
            notification = get_object_or_404(
                Notificacao.objects.select_for_update(),
                pk=pk,
                utilizador_id=request.user.pk,
            )
            if notification.lida_em is None:
                notification.lida_em = timezone.now()
                notification.save(update_fields=("lida_em",))

        return Response(NotificacaoSerializer(notification).data)


class TipoTrabalhoListView(generics.ListAPIView):
    serializer_class = TipoTrabalhoSerializer
    permission_classes = (IsAdministrator,)

    def get_queryset(self):
        return TipoTrabalho.objects.order_by("nome", "pk")


class TemplateEtapaListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAdministrator,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TemplateEtapaCreateSerializer
        return TemplateEtapaSerializer

    def get_queryset(self):
        return TemplateEtapa.objects.filter(
            tipo_trabalho_id=self.kwargs["tipo_trabalho_id"]
        ).order_by("ordem", "pk")

    def perform_create(self, serializer):
        with transaction.atomic():
            work_type = get_object_or_404(
                TipoTrabalho.objects.select_for_update(),
                pk=self.kwargs["tipo_trabalho_id"],
            )
            highest_order = TemplateEtapa.objects.filter(
                tipo_trabalho=work_type
            ).aggregate(highest_order=Max("ordem"))["highest_order"] or 0
            template = serializer.save(
                tipo_trabalho=work_type,
                ordem=highest_order + 1,
                ativa=True,
            )
            now = timezone.now()
            open_work_ids = list(
                Trabalho.objects.select_for_update()
                .filter(tipo_trabalho=work_type)
                .exclude(estado__in=("Concluído", "Entregue"))
                .values_list("pk", flat=True)
            )
            for work_id in open_work_ids:
                EtapaTrabalho.objects.filter(
                    trabalho_id=work_id,
                    ordem__gte=template.ordem,
                ).update(ordem=F("ordem") + 1, atualizada_em=now)
                EtapaTrabalho.objects.create(
                    trabalho_id=work_id,
                    template_etapa=template,
                    nome=template.nome_etapa,
                    ordem=template.ordem,
                    estado="Por Iniciar",
                    ativa=template.ativa,
                    criada_em=now,
                    atualizada_em=now,
                )


class TemplateEtapaUpdateView(generics.UpdateAPIView):
    serializer_class = TemplateEtapaSerializer
    permission_classes = (IsAdministrator,)
    queryset = TemplateEtapa.objects.select_for_update()

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            template_type_id = TemplateEtapa.objects.filter(
                pk=kwargs["pk"]
            ).values_list("tipo_trabalho_id", flat=True).first()
            if template_type_id is not None:
                get_object_or_404(
                    TipoTrabalho.objects.select_for_update(),
                    pk=template_type_id,
                )
            return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        template = serializer.instance
        old_order = template.ordem
        new_order = serializer.validated_data.get("ordem", old_order)
        now = timezone.now()
        open_work_ids = list(
            Trabalho.objects.select_for_update()
            .filter(tipo_trabalho_id=template.tipo_trabalho_id)
            .exclude(estado__in=("Concluído", "Entregue"))
            .values_list("pk", flat=True)
        )

        if new_order < old_order:
            EtapaTrabalho.objects.filter(
                trabalho_id__in=open_work_ids,
                ordem__gte=new_order,
                ordem__lt=old_order,
            ).update(ordem=F("ordem") + 1, atualizada_em=now)
            TemplateEtapa.objects.filter(
                tipo_trabalho_id=template.tipo_trabalho_id,
                ordem__gte=new_order,
                ordem__lt=old_order,
            ).exclude(pk=template.pk).update(ordem=F("ordem") + 1)
        elif new_order > old_order:
            EtapaTrabalho.objects.filter(
                trabalho_id__in=open_work_ids,
                ordem__gt=old_order,
                ordem__lte=new_order,
            ).update(ordem=F("ordem") - 1, atualizada_em=now)
            TemplateEtapa.objects.filter(
                tipo_trabalho_id=template.tipo_trabalho_id,
                ordem__gt=old_order,
                ordem__lte=new_order,
            ).exclude(pk=template.pk).update(ordem=F("ordem") - 1)

        updated_template = serializer.save()
        stage_updates = {}
        if "nome_etapa" in serializer.validated_data:
            stage_updates["nome"] = updated_template.nome_etapa
        if "ordem" in serializer.validated_data:
            stage_updates["ordem"] = updated_template.ordem
        if "ativa" in serializer.validated_data:
            stage_updates["ativa"] = updated_template.ativa
        if stage_updates:
            stage_updates["atualizada_em"] = now
            EtapaTrabalho.objects.filter(
                template_etapa=updated_template,
                trabalho_id__in=open_work_ids,
            ).update(**stage_updates)


class TrabalhoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TrabalhoSerializer
    permission_classes = (HasLaboratoryProfile,)

    def get_queryset(self):
        user = self.request.user
        role = get_user_role(user)
        queryset = Trabalho.objects.select_related(
            "encomenda",
            "encomenda__cliente",
            "tipo_trabalho",
        )

        if role == ADMINISTRATOR:
            return queryset.order_by("-criado_em")
        if role == COLLABORATOR:
            return queryset.exclude(
                estado__in=("Em Avaliação", "Concluído", "Entregue")
            ).order_by("-criado_em")
        if role == CLIENT:
            return queryset.filter(
                encomenda__cliente__utilizador_id=user.pk
            ).order_by("-criado_em")
        return queryset.none()


class PermissaoColaboradorListCreateView(generics.ListCreateAPIView):
    serializer_class = PermissaoColaboradorSerializer
    permission_classes = (IsAdministrator,)

    def get_queryset(self):
        return PermissaoColaborador.objects.filter(
            colaborador_id=self.kwargs["colaborador_id"]
        ).order_by("codigo")

    def perform_create(self, serializer):
        colaborador = get_object_or_404(
            Colaborador,
            pk=self.kwargs["colaborador_id"],
        )
        serializer.save(
            colaborador=colaborador,
            concedida_por=self.request.user,
        )


class PermissaoColaboradorDeleteView(generics.DestroyAPIView):
    serializer_class = PermissaoColaboradorSerializer
    permission_classes = (IsAdministrator,)
    lookup_field = "codigo"

    def get_queryset(self):
        return PermissaoColaborador.objects.filter(
            colaborador_id=self.kwargs["colaborador_id"]
        )


class EncomendaRececaoListView(generics.ListAPIView):
    serializer_class = EncomendaRececaoSerializer
    permission_classes = (HasDelegatedPermission,)
    permission_code = RECECAO_TRABALHOS

    def get_queryset(self):
        return Encomenda.objects.filter(estado="Em Avaliação").select_related(
            "cliente"
        ).order_by("data_criacao")
