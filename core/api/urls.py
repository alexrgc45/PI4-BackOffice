from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminPasswordChangeView,
    AdminProfileView,
    AdminWorkFileDownloadView,
    AdminWorkCreateView,
    ClienteDetailView,
    ClienteListCreateView,
    ColaboradorDetailView,
    ColaboradorListView,
    CurrentUserView,
    EncomendaRececaoListView,
    NotificacaoListView,
    NotificacaoMarkReadView,
    PermissaoColaboradorDeleteView,
    PermissaoColaboradorListCreateView,
    TemplateEtapaListCreateView,
    TemplateEtapaUpdateView,
    TokenObtainView,
    TokenRefreshView,
    TrabalhoViewSet,
    TipoTrabalhoListView,
    UtilizadorPendenteApproveView,
    UtilizadorPendenteListView,
    UtilizadorPendenteRejectView,
)

app_name = "api"

router = DefaultRouter()
router.register("trabalhos", TrabalhoViewSet, basename="trabalho")

urlpatterns = [
    path("auth/token/", TokenObtainView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("admin/perfil/", AdminProfileView.as_view(), name="admin-profile"),
    path(
        "admin/perfil/alterar-palavra-passe/",
        AdminPasswordChangeView.as_view(),
        name="admin-password-change",
    ),
    path(
        "admin/trabalhos/",
        AdminWorkCreateView.as_view(),
        name="admin-work-create",
    ),
    path(
        "admin/ficheiros/<int:pk>/",
        AdminWorkFileDownloadView.as_view(),
        name="admin-work-file-download",
    ),
    path("clientes/", ClienteListCreateView.as_view(), name="cliente-list"),
    path("clientes/<int:pk>/", ClienteDetailView.as_view(), name="cliente-detail"),
    path("colaboradores/", ColaboradorListView.as_view(), name="colaborador-list"),
    path(
        "colaboradores/<int:pk>/",
        ColaboradorDetailView.as_view(),
        name="colaborador-detail",
    ),
    path(
        "utilizadores/pendentes/",
        UtilizadorPendenteListView.as_view(),
        name="utilizador-pendente-list",
    ),
    path(
        "utilizadores/<int:pk>/aprovar/",
        UtilizadorPendenteApproveView.as_view(),
        name="utilizador-pendente-aprovar",
    ),
    path(
        "utilizadores/<int:pk>/rejeitar/",
        UtilizadorPendenteRejectView.as_view(),
        name="utilizador-pendente-rejeitar",
    ),
    path("notificacoes/", NotificacaoListView.as_view(), name="notificacao-list"),
    path(
        "notificacoes/<int:pk>/ler/",
        NotificacaoMarkReadView.as_view(),
        name="notificacao-marcar-lida",
    ),
    path("tipos-trabalho/", TipoTrabalhoListView.as_view(), name="tipo-trabalho-list"),
    path(
        "tipos-trabalho/<int:tipo_trabalho_id>/etapas/",
        TemplateEtapaListCreateView.as_view(),
        name="tipo-trabalho-etapas",
    ),
    path(
        "etapas-template/<int:pk>/",
        TemplateEtapaUpdateView.as_view(),
        name="template-etapa-update",
    ),
    path(
        "permissoes/colaboradores/<int:colaborador_id>/",
        PermissaoColaboradorListCreateView.as_view(),
        name="colaborador-permissoes",
    ),
    path(
        "permissoes/colaboradores/<int:colaborador_id>/<str:codigo>/",
        PermissaoColaboradorDeleteView.as_view(),
        name="colaborador-permissao-revogar",
    ),
    path("encomendas/rececao/", EncomendaRececaoListView.as_view(), name="rececao"),
] + router.urls
