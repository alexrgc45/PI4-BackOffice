from django.shortcuts import render


def login_page(request):
    return render(request, "core/login.html")


def dashboard(request):
    return render(
        request,
        "core/dashboard.html",
        {"active_page": "dashboard"},
    )


def work_list(request):
    return render(
        request,
        "core/work_list.html",
        {"active_page": "works"},
    )


def work_create(request):
    return render(
        request,
        "core/work_create.html",
        {"active_page": "works"},
    )


def reception_work_list(request):
    return render(
        request,
        "core/reception_work_list.html",
        {"active_page": "reception"},
    )


def work_history(request):
    return render(
        request,
        "core/work_history.html",
        {"active_page": "history"},
    )


def client_list(request):
    return render(
        request,
        "core/client_list.html",
        {"active_page": "clients"},
    )


def client_create(request):
    return render(
        request,
        "core/client_create.html",
        {"active_page": "clients", "is_editing": False},
    )


def client_edit(request, client_id):
    return render(
        request,
        "core/client_create.html",
        {
            "active_page": "clients",
            "client_id": client_id,
            "is_editing": True,
        },
    )


def collaborator_list(request):
    return render(
        request,
        "core/collaborator_list.html",
        {"active_page": "collaborators"},
    )


def collaborator_edit(request, collaborator_id):
    return render(
        request,
        "core/collaborator_edit.html",
        {
            "active_page": "collaborators",
            "collaborator_id": collaborator_id,
        },
    )


def pending_user_list(request):
    return render(
        request,
        "core/pending_user_list.html",
        {"active_page": "pending_users"},
    )


def notification_list(request):
    return render(
        request,
        "core/notification_list.html",
        {"active_page": "notifications"},
    )


def permission_list(request):
    return render(
        request,
        "core/permission_list.html",
        {"active_page": "permissions"},
    )


def stage_configuration(request):
    return render(
        request,
        "core/stage_configuration.html",
        {"active_page": "stages"},
    )


def admin_profile(request):
    return render(
        request,
        "core/admin_profile.html",
        {"active_page": "profile"},
    )
