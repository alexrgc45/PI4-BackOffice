from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.login_page, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("trabalhos/", views.work_list, name="work_list"),
]
