from html import escape

from django.http import HttpRequest, HttpResponse


def page(title: str, content: str) -> str:
    """Сформировать единый HTML-каркас страницы."""
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
        "/dist/css/bootstrap.min.css"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <link rel="stylesheet" href="{bootstrap}">
    <style>
        body {{ background-color: #f8f9fa; }}
        main {{ min-height: calc(100vh - 130px); }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg bg-dark mb-4" data-bs-theme="dark">
        <div class="container">
            <a class="navbar-brand" href="/">Учёт техники</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/devices/">Устройства</a>
                <a class="nav-link" href="/rooms/">Помещения</a>
            </div>
        </div>
    </nav>
    <main class="container">{content}</main>
    <footer class="container py-4 text-secondary">
        Практическая работа № 5 · Django 5.2
    </footer>
</body>
</html>"""


def html_response(content: str, status: int = 200) -> HttpResponse:
    """Вернуть HTML с явной UTF-8-кодировкой."""
    return HttpResponse(
        content.encode("utf-8"),
        status=status,
        content_type="text/html; charset=utf-8",
    )


def index(request: HttpRequest) -> HttpResponse:
    """Показать главную страницу проекта."""
    content = """
    <section class="p-5 mb-4 bg-white rounded-3 shadow-sm">
        <h1 class="display-5 fw-bold">Сервис учёта бытовой техники</h1>
        <p class="lead">
            Веб-интерфейс для просмотра устройств, их состояния
            и размещения по помещениям.
        </p>
        <a href="/devices/" class="btn btn-primary me-2">
            Устройства
        </a>
        <a href="/rooms/" class="btn btn-outline-secondary">
            Помещения
        </a>
    </section>
    """
    return html_response(page("Учёт техники", content))


def page_not_found(
    request: HttpRequest,
    exception: Exception,
) -> HttpResponse:
    """Вернуть оформленную страницу для неизвестного URL."""
    content = """
    <div class="alert alert-danger" role="alert">
        <h1 class="alert-heading">404 — страница не найдена</h1>
        <p>Проверьте адрес или вернитесь на главную страницу.</p>
        <a href="/" class="btn btn-primary">На главную</a>
    </div>
    """
    return html_response(
        page("404 — страница не найдена", content),
        status=404,
    )
