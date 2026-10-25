from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Показать главную страницу проекта."""
    return render(request, "homepage/index.html")


def page_not_found(
    request: HttpRequest,
    exception: Exception,
) -> HttpResponse:
    """Вернуть оформленную страницу для неизвестного URL."""
    return render(request, "404.html", status=404)
