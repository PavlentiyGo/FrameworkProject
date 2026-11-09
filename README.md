# Сервис учёта бытовой техники

Учебный индивидуальный проект: реестр устройств, их характеристик,
размещения, состояния и рекомендаций по обслуживанию. Консольная версия
ПР1–ПР3 работает с JSON; веб-версия ПР5–ПР6 получила SQL-слой в ПР7,
а в ПР9 переведена на Django ORM.

## Возможности веб-версии

- Списки помещений и техники, подробные карточки и связанные ссылки.
- Поиск по названию либо по названию, типу, производителю и модели.
- Совместные фильтры по помещению, состоянию и максимальной стоимости.
- Скрытие списанных устройств и поиск техники для обслуживания.
- Сортировка по названию, цене, году или помещению и названию.
- Пагинация по 2, 5, 10, 20 или 50 устройств с сохранением параметров GET.
- Помещения без действующей техники; списанная техника не занимает помещение.
- Статистика количества и стоимости, группировка по помещениям и состояниям,
  фильтрация групп по минимальному количеству устройств.
- Создание, изменение и удаление объектов через Django admin и Django shell.
- Проверка ввода, пустые результаты и страницы с HTTP 404.

## Технологии

Python 3.10+, Django 5.2, SQLite, Django ORM, DTL, Bootstrap 5.3.3,
CSS и JavaScript. Проверки: pytest, pytest-django, flake8, Pyright.
`django-stubs` описывает типы Django для статического анализатора.
Текущее окружение и `pyrightconfig.json` настроены на Python 3.14.

## Установка и запуск

Из корня проекта, где находится `manage.py`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py import_pr7
python manage.py check
python manage.py runserver --insecure
```

Открыть <http://127.0.0.1:8000/>. При `DEBUG=False` флаг `--insecure`
нужен учебному серверу для локальной отдачи статики. При `DEBUG=True`
достаточно `python manage.py runserver`. Bootstrap загружается с CDN.

Создание администратора:

```bash
python manage.py createsuperuser
```

Далее открыть <http://127.0.0.1:8000/admin/>. Администраторы Django
и пользователи предметной области — отдельные учётные записи.
Пользователи из JSON не получают права входа в admin автоматически.

## Модели ПР9

| Модель | Приложение | Поля и ограничения |
|---|---|---|
| `Room` | `rooms` | `id`, уникальное обязательное `name` |
| `Condition` | `conditions` | `id`, уникальное `name` из четырёх допустимых состояний |
| `User` | `users` | `id`, уникальный `login`, `password` с хешем Django |
| `Device` | `equipment` | `id`, `name`, `device_type`, `manufacturer`, `model`, `purchase_year`, `price`, `room`, `condition`, `service_interval` |

`id` создаётся Django как `BigAutoField(primary_key=True)`.
Обязательные поля не допускают NULL и пустого ввода (`null=False`,
`blank=False`). Интервал обслуживания по умолчанию равен 3 годам.
Цена хранится как `DecimalField(max_digits=12, decimal_places=2)`.
Валидаторы проверяют год покупки от 1900 до текущего, неотрицательную цену
и положительный интервал. Ограничения БД дополнительно защищают цену,
минимальный год, интервал, непустые названия и допустимые состояния.

Связи «один ко многим»:

```text
Room      1 ── N Device: room = ForeignKey(..., PROTECT, related_name="devices")
Condition 1 ── N Device: condition = ForeignKey(..., PROTECT, related_name="devices")
```

Удаление используемого помещения или состояния запрещено `PROTECT`.
Прямые связи: `device.room`, `device.condition`; обратные:
`room.devices.all()`, `condition.devices.all()`.
`device.room_id` — числовой внешний ключ, `device.room` — объект модели.
Связь с пользователем не добавлялась: в исходном проекте ПР7 её не было.
Методы `is_available()` и `get_service_status()` сохраняют правила ПР3.

## Базы данных и перенос из ПР7

- `data/appliances.sqlite` — исходная база ПР7 с таблицами `rooms`,
  `users`, `conditions`, `devices`. Сохранена в репозитории как учебный источник.
- `db.sqlite3` — рабочая база Django: служебные таблицы и новые таблицы
  `rooms_room`, `users_user`, `conditions_condition`, `equipment_device`.
  Путь задан в `DATABASES`; файл исключён из Git.
- `data/*.json` — сохранённые исходные данные и хранилище консольной версии.

Выбрана стратегия создания новых таблиц миграциями и отдельного переноса.
Настройка `DATABASES` не переключается на исходный файл ПР7.
Команда `python manage.py import_pr7` вызывает `db.orm_import.import_pr7()`:

1. Открывает исходную SQLite-базу в `mode=ro` и проверяет внешние ключи.
2. Читает помещения, состояния, пользователей и устройства.
3. Сохраняет их через ORM в одной транзакции, в порядке зависимостей.
4. Сохраняет исходные ID, `room_id`, `condition_id`; цену приводит к Decimal.
5. Пароли пользователей преобразует в хеши Django.
6. Совпадающие записи при повторном запуске пропускает. Конфликт значений
   вызывает ошибку и откат всех вставок текущего запуска; перезаписи нет.

Другой источник можно указать явно:

```bash
python manage.py import_pr7 --source data/appliances.sqlite
```

До перехода созданы локальные резервные копии `db.sqlite3.pr9-backup`
и `data/appliances.sqlite.pr9-backup`. Они исключены из Git.
JSON и исходная база не синхронизируются с рабочей ORM-базой:
редактирование в admin меняет только `db.sqlite3`. Повторный импорт после
изменения записи сообщает о конфликте, чтобы не затереть изменения.

SQL-код `db/database.py`, `db/import_json.py`, `db/queries.py`,
`db/check_queries.py`, `sql/schema.sql`, `sql/queries.sql` сохранён как
результат ПР7. Прямые SQL-запросы в текущих view-функциях отсутствуют.
В ПР9 SQL используется только для чтения старого формата при переносе
и в сохранённых учебных командах ПР7.

## Страницы

| URL | Назначение |
|---|---|
| `/` | Главная |
| `/devices/` | Список, фильтры, сортировка, пагинация |
| `/devices/<int:device_id>/` | Устройство, состояние, обслуживание |
| `/devices/search/` | Форма поиска, фильтры и постраничные результаты |
| `/devices/statistics/` | Общая статистика, группировки, обслуживание |
| `/rooms/` | Помещения с количеством устройств |
| `/rooms/<int:room_id>/` | Помещение и связанные устройства |
| `/rooms/available/` | Помещения без действующей техники |
| `/admin/` | CRUD моделей через встроенную административную панель |

Примеры:

```text
/devices/?sort=room&page_size=5&page=2
/devices/?page_size=2&page=2
/devices/search/?q=Samsung&scope=all&room_id=2&condition=исправно&sort=price
/devices/?hide_retired=on&needs_service=on
/devices/statistics/?min_count=2
```

Сначала применяется поиск и фильтры, затем сортировка, затем `Paginator`.
Допустимые сортировки перечислены в `equipment.queries.SORT_FIELDS`;
произвольный параметр GET не передаётся в `order_by()`.
В сортировке есть `pk` как дополнительный ключ для стабильных страниц.
Форма при изменении фильтров сбрасывает номер страницы, а навигация сохраняет
остальные параметры. Нечисловой `page` открывает первую страницу,
нулевой, отрицательный или слишком большой — последнюю (`get_page()`).
На исходных трёх устройствах пагинацию можно увидеть, выбрав по 2 на странице.
Ошибки фильтров, сортировки и размера страницы показываются в форме.
Ненайденный объект возвращает HTTP 404. Пустые выборки обрабатываются
через `{% empty %}`. `icontains` безопасно экранирует SQL-метасимволы.
SQLite по умолчанию различает регистр кириллицы в LIKE, как и в ПР7;
например, для «Холодильник» следует искать «Холод».

Пример «свободные помещения на дату» из Roomly адаптирован к предметной
области: здесь нет бронирований и дат занятости. Поиск доступной техники
выполняется по состоянию «исправно», поиск свободных помещений — по
отсутствию несписанной техники.

## ORM-запросы и проверка минимального объёма

Запросы реализованы в `equipment/queries.py`, `rooms/views.py`,
`equipment/views.py`, `equipment/forms.py` и используются страницами.
Ниже перечислены различные выборки, а не отдельные методы одной цепочки.

| № | Выборка | Применение |
|---|---|---|
| 1 | `Room.objects.all()` | Помещения в форме поиска |
| 2 | `Device.objects.select_related("room", "condition")` | Списки без N+1 |
| 3 | `.get(pk=device_id)` | Карточка устройства |
| 4 | `Room.objects.get(pk=room_id)` | Карточка помещения |
| 5 | `.filter(room=room)` | Фильтр техники по помещению |
| 6 | `.filter(condition__name=condition)` | Фильтр по связанной модели |
| 7 | `.filter(room=room, condition__name=condition)` | Совместные условия |
| 8 | `.filter(price__lte=max_price)` | Ограничение стоимости |
| 9 | `.exclude(condition__name="списано")` | Скрытие неактуальной техники |
| 10 | `.filter(name__icontains=term)` | Поиск по одному полю |
| 11 | `.filter(Q(...) \| Q(...) \| Q(...) \| Q(...))` | Поиск по четырём полям |
| 12 | `.order_by("name", "pk")` | Сортировка по названию |
| 13 | `.order_by("room__name", "name", "pk")` | Сортировка по связанному полю |
| 14 | `Room.objects.annotate(device_count=Count("devices"))` | Карточки помещений |
| 15 | `room.devices.select_related("room", "condition")` | Обратная связь |
| 16 | `Device.objects.aggregate(...)` | COUNT, SUM, AVG, MIN, MAX |
| 17 | `Room.objects.annotate(...).filter(device_count__gte=...)` | Группировка и HAVING |
| 18 | `Condition.objects.annotate(...)` | Группировка по состояниям |
| 19 | `exclude(...).filter(Q(...) \| Q(... F(...)))` | Требующие обслуживания |
| 20 | `Room.objects.exclude(pk__in=active_room_ids)` | Помещения без действующей техники |
| 21 | `Condition.objects.values_list("name", "name")` | Только нужные поля для выбора состояния |
| 22 | `Paginator(queryset, page_size).get_page(page)` | Ограничение результата страницей |

Для подзапроса доступности также используется `.values("room_id")`.
Списанные устройства исключены из стоимости действующей техники.
Агрегаты для пустой БД возвращают ноль, годы — `None`. LEFT JOIN,
используемый при аннотировании, сохраняет помещения и состояния без устройств.
Объекты для обслуживания исключают списанную и уже ремонтируемую технику.

## CRUD через Django shell

```bash
python manage.py shell
```

```python
from decimal import Decimal
from rooms.models import Room
from conditions.models import Condition
from equipment.models import Device

room = Room.objects.create(name="Тестовая мастерская")
device = Device.objects.create(
    name="Дрель", device_type="Инструмент", manufacturer="Bosch",
    model="GSR", purchase_year=2025, price=Decimal("5000.00"),
    room=room, condition=Condition.objects.get(name="исправно"),
)
device.name = "Шуруповёрт"
device.full_clean()
device.save(update_fields=["name"])
print(Device.objects.get(pk=device.pk).name)
device.change_condition("в ремонте")
device.save(update_fields=["condition"])
print(room.devices.all())
# room.delete() сейчас запрещён из-за связанного устройства (PROTECT).
device.delete()
room.delete()
```

Присваивание изменяет объект в памяти, `save()` сохраняет изменения.
`full_clean()` проверяет модель, но не вызывается автоматически из `save()`;
в admin проверку выполняет ModelForm, а импорт вызывает её явно.

## Структура проекта

```text
manage.py                  # команды Django
appliance_service/         # settings, urls, WSGI/ASGI
equipment/                 # Device, ORM-запросы, формы, страницы, admin
  migrations/              # версия структуры таблицы Device
  management/commands/     # команда import_pr7
rooms/                     # Room, страницы помещений, admin, миграции
conditions/                # Condition, admin, миграции
users/                     # User предметной области, admin, миграции
homepage/                  # главная, 404, static/homepage/{css,js,img}
templates/                 # base, 404, includes/{navigation,pagination}
db/orm_import.py           # перенос из SQLite ПР7 в ORM
db/, sql/                  # сохранённый SQL-слой ПР7
models.py, devices.py      # предметные классы и логика CLI из ПР3
storage.py, main.py        # JSON и консольная версия
data/                      # исходная SQLite-база и JSON
tests/                     # CLI, SQL ПР7, ORM, перенос и веб-сценарии
```

Все страницы наследуют `templates/base.html`; карточки и навигация вынесены
в include-шаблоны. ORM-объекты передаются через контекст в `render()`.
Связанные значения: `device.room.name`, `device.condition.name`.
Именованные URL, DTL-фильтры, экранирование, статика и обработка 404 сохранены.

## Проверка

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
pytest -v
flake8 -j 1 .
pyright
```

`-j 1` отключает создание рабочих процессов flake8, что удобно в ограниченном
окружении. Для автоматически сгенерированных миграций исключена только
проверка длины строк E501. `django-stubs` позволяет Pyright понимать поля,
менеджеры и QuerySet Django без отключения проверок типов.

ORM-тесты работают с отдельной тестовой базой Django. SQL-тесты ПР7 используют
временный SQLite-файл. Рабочие базы тестами не изменяются. Проверяются CRUD,
ограничения и связи, защита удаления, повторный импорт и его откат, неизменность
источника, выборки, отсутствие N+1, статистика, сортировка, пагинация,
сохранение GET-параметров, admin, экранирование, пустые выборки и HTTP 404.

Проверка исторического SQL-слоя ПР7:

```bash
python -m db.check_queries
```

## Консольная версия

```bash
python main.py
```

Демонстрационный логин `owner@example.com`, пароль `home2026`.
CLI продолжает использовать JSON, поддерживает операции с техникой,
авторизацию, поиск, фильтрацию и статистику. Его изменения не синхронизируются
с Django ORM автоматически.
