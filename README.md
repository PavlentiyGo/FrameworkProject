# Сервис учёта бытовой техники

Учебное приложение для ведения домашнего или офисного реестра техники.
Консольная версия, созданная в ПР1–ПР3, дополнена в ПР5 базовым
веб-интерфейсом на Django. В ПР6 веб-часть переведена на Django Template
Language (DTL): HTML находится в шаблонах, а представления подготавливают
данные и передают их через контекст в `render()`.

## Возможности

Веб-интерфейс позволяет:

- просматривать список устройств;
- открывать карточку устройства;
- видеть состояние и рекомендацию по обслуживанию;
- просматривать помещения;
- видеть устройства выбранного помещения;
- переходить между связанными страницами;
- получать понятные страницы с кодом HTTP 404.

Консольная версия дополнительно поддерживает добавление, поиск, сортировку,
фильтрацию, изменение и удаление устройств, назначение помещений и статистику.

## Технологии

- Python 3.10 или новее;
- Django 5.2;
- HTML и CSS;
- Django Template Language и JavaScript;
- Bootstrap 5.3;
- JSON;
- pytest и pytest-django;
- flake8;
- Pyright и Pylance.

## Предметная область

- `Device` — устройство с названием, типом, производителем, моделью, годом,
  стоимостью, состоянием и интервалом обслуживания;
- `Room` — помещение, в котором находится техника;
- `User` — пользователь консольного приложения.

Объект `Device` содержит ссылку на объект `Room`. Классы ПР3 остаются в
`models.py` и пока не являются моделями Django ORM.

## Структура проекта

```text
.
├── manage.py
├── appliance_service/     # настройки и корневая маршрутизация Django
├── templates/
│   ├── base.html          # общий каркас, блоки title и content, статика
│   ├── 404.html           # неизвестный URL
│   └── includes/
│       └── navigation.html
├── homepage/
│   ├── templates/homepage/index.html
│   ├── static/homepage/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   └── img/logo.svg
│   └── views.py           # главная страница и обработчик 404
├── equipment/
│   ├── templates/equipment/
│   │   ├── device_list.html
│   │   ├── device_detail.html
│   │   └── includes/
│   │       ├── device_card.html
│   │       └── device_condition.html
│   └── views.py
├── rooms/
│   ├── templates/rooms/
│   │   ├── room_list.html
│   │   ├── room_detail.html
│   │   └── includes/room_card.html
│   └── views.py
├── models.py              # классы Device, Room и User из ПР3
├── devices.py             # предметная логика и операции с коллекциями
├── storage.py             # загрузка и сохранение JSON
├── main.py                # сохранённая консольная версия
├── data/
│   ├── devices.json
│   ├── rooms.json
│   ├── users.json
│   └── conditions.json
├── tests/                 # тесты ПР3, веб-интерфейса и шаблонов ПР6
└── requirements.txt
```

## Страницы веб-интерфейса

| URL | View-функция | Назначение |
|---|---|---|
| `/` | `homepage.views.index` | Главная страница |
| `/devices/` | `equipment.views.device_list` | Список устройств |
| `/devices/<int:device_id>/` | `equipment.views.device_detail` | Карточка устройства |
| `/rooms/` | `rooms.views.room_list` | Список помещений |
| `/rooms/<int:room_id>/` | `rooms.views.room_detail` | Карточка помещения |

Для неизвестного URL используется `homepage.views.page_not_found`. Если
динамический URL существует, но объект с переданным ID отсутствует,
соответствующая view-функция возвращает собственную страницу со статусом 404.
В шаблон карточки при этом передаётся `None`, и сообщение выводится через
`{% if %}` / `{% else %}` с сохранением HTTP-статуса 404.

## Шаблоны Django (ПР6)

Общие шаблоны находятся в `templates/`, а шаблоны приложений — в их каталогах
`templates/<имя приложения>/`. В `settings.py` настроены
`"DIRS": [BASE_DIR / "templates"]` и `APP_DIRS=True`.

Все страницы наследуют `base.html` через `{% extends "base.html" %}` и
переопределяют блоки `{% block title %}` и `{% block content %}`.
Веб-представления больше не формируют HTML-строки; функции `page()` и
`html_response()` удалены.

Повторяющиеся части подключаются через `{% include %}`:

- `includes/navigation.html` — общая навигация с активным разделом;
- `rooms/includes/room_card.html` — карточка помещения;
- `equipment/includes/device_card.html` — устройство в общем списке и помещении;
- `equipment/includes/device_condition.html` — состояние устройства в карточках
  и на подробной странице.

Представления передают реальные объекты `Room` и `Device` через словарь
контекста. В списке помещений `rooms` содержит объекты помещений, а
`room_cards` — помещения вместе с подсчитанным числом устройств. Данные
включаемым карточкам передаются явно через `with ... only`.

Списки формируются через `{% for %}`, отсутствие данных обрабатывается через
`{% empty %}`. Условия `{% if %}` выбирают цвет состояния устройства,
сообщение о доступности и ветку отсутствующего объекта. Рекомендации по
обслуживанию вычисляются существующим методом `Device.get_service_status()`
во view, а не средствами шаблона.

Фильтры применяются к данным проекта:

- `{{ devices|length }}` и `{{ rooms|length }}` — количество элементов;
- `{{ room.name|default:"Без названия" }}` — запасной текст;
- `{{ device.price|floatformat:"2" }}` — стоимость с двумя десятичными знаками;
- `{{ device.purchase_year|stringformat:"d" }}` — год без разделителя тысяч.

Django автоматически экранирует пользовательские данные при выводе.

## Именованные URL

В приложениях сохранены `app_name` и существующие имена маршрутов:

| Имя маршрута | Адрес |
|---|---|
| `homepage:index` | `/` |
| `equipment:device_list` | `/devices/` |
| `equipment:device_detail` | `/devices/<int:device_id>/` |
| `rooms:room_list` | `/rooms/` |
| `rooms:room_detail` | `/rooms/<int:room_id>/` |

Внутренние ссылки во всех шаблонах строятся через `{% url %}`. Например:

```django
{% url 'equipment:device_detail' device.id %}
{% url 'rooms:room_detail' device.room.id %}
```

## Статические файлы

`django.contrib.staticfiles` находит ресурсы в `homepage/static/homepage/`:

- `css/style.css` — общий фон, карточки, состояния устройств, логотип и подвал;
- `img/logo.svg` — собственная иконка бытовой техники в навигации;
- `js/main.js` — автоматически устанавливает текущий год в подвале.

Базовый шаблон и навигация используют `{% load static %}` и `{% static %}`.
Собственный CSS подключается после Bootstrap 5.3.3; Bootstrap загружается
с CDN, поэтому для его получения браузеру нужен доступ к интернету.

Проверка обнаружения статических файлов:

```bash
python manage.py findstatic homepage/css/style.css homepage/js/main.js homepage/img/logo.svg
```

## Хранение данных

Предметные данные на этапе ПР6 продолжают храниться в JSON. Функции
`storage.py` преобразуют JSON-объекты в `Device`, `Room`, `User` и обратно.
Веб-страницы используют те же функции, что и консольная версия.

После `migrate` Django создаёт локальную `db.sqlite3` для своих служебных
приложений. Перенос предметных сущностей в Django ORM выполняется в следующих
практических работах.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
```

## Запуск веб-версии

```bash
source .venv/bin/activate
python manage.py check
python manage.py runserver --insecure
```

После запуска открыть <http://127.0.0.1:8000/>.

Сейчас в настройках установлено `DEBUG=False`. Флаг `--insecure` разрешает
учебному серверу Django отдавать собственные CSS, JS и изображение при этом
значении. Он используется только для локальной разработки. Если установить
`DEBUG=True`, достаточно обычного `python manage.py runserver`; для
неизвестных URL в этом режиме Django покажет диагностическую страницу 404.

## Запуск консольной версии

```bash
source .venv/bin/activate
python main.py
```

Демонстрационная учётная запись:

- логин: `owner@example.com`;
- пароль: `home2026`.

## Проверка проекта

```bash
pytest -v
flake8 .
pyright
python manage.py check
```

## Текущее состояние и дальнейшее развитие

В ПР5 добавлены Django-проект, три приложения, двухуровневая маршрутизация,
view-функции, динамические URL, HTML, Bootstrap, навигация и обработка 404.

На следующих этапах планируются Django ORM, формы, веб-авторизация и
редактирование данных через браузер.
