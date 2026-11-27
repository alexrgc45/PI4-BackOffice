from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.login_page, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("trabalhos/", views.work_list, name="work_list"),
    path("trabalhos/criar/", views.work_create, name="work_create"),
    path("rececao-trabalhos/", views.reception_work_list, name="reception_work_list"),
    path("historico/", views.work_history, name="history"),
    path("clientes/criar/", views.client_create, name="client_create"),
    path("clientes/<int:client_id>/editar/", views.client_edit, name="client_edit"),
    path("clientes/", views.client_list, name="client_list"),
    path("colaboradores/", views.collaborator_list, name="collaborator_list"),
    path(
        "colaboradores/<int:collaborator_id>/editar/",
        views.collaborator_edit,
        name="collaborator_edit",
    ),
    path("aceitar-utilizadores/", views.pending_user_list, name="pending_user_list"),
    path("notificacoes/", views.notification_list, name="notification_list"),
    path("permissoes/", views.permission_list, name="permission_list"),
    path("configuracao-etapas/", views.stage_configuration, name="stage_configuration"),
    path("perfil/", views.admin_profile, name="admin_profile"),
]
