from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.welcome_page, name="welcome"),
    path("login/", views.login_page, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("trabalhos/", views.work_list, name="work_list"),
    path("rececao-trabalhos/", views.reception_work_list, name="reception_work_list"),
    path("historico/", views.work_history, name="history"),
    path("clientes/", views.client_list, name="client_list"),
    path("colaboradores/", views.collaborator_list, name="collaborator_list"),
    path("aceitar-utilizadores/", views.pending_user_list, name="pending_user_list"),
    path("notificacoes/", views.notification_list, name="notification_list"),
    path("permissoes/", views.permission_list, name="permission_list"),
    path("configuracao-etapas/", views.stage_configuration, name="stage_configuration"),
    path("perfil/", views.admin_profile, name="admin_profile"),
]
