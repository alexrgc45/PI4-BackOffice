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
