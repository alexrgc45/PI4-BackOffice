from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Colaborador, Encomenda, PermissaoColaborador, Trabalho

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
    CurrentUserSerializer,
    EncomendaRececaoSerializer,
    PermissaoColaboradorSerializer,
    TokenObtainSerializer,
    TrabalhoSerializer,
)


class TokenObtainView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = TokenObtainSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class CurrentUserView(APIView):
    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)


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
