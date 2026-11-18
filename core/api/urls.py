from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CurrentUserView,
    EncomendaRececaoListView,
    PermissaoColaboradorDeleteView,
    PermissaoColaboradorListCreateView,
    TokenObtainView,
    TrabalhoViewSet,
)

app_name = "api"

router = DefaultRouter()
router.register("trabalhos", TrabalhoViewSet, basename="trabalho")

urlpatterns = [
    path("auth/token/", TokenObtainView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
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
