"""Проверка параметров поиска, сортировки и пагинации ПР9."""

from django import forms

from rooms.models import Room


class DeviceSearchForm(forms.Form):
    q = forms.CharField(
        label="Название, тип или производитель", required=False,
        max_length=150,
    )
    room_id = forms.ModelChoiceField(
        label="Помещение", required=False, queryset=Room.objects.all(),
        empty_label="Все помещения",
    )
    condition = forms.ChoiceField(label="Состояние", required=False)
    max_price = forms.DecimalField(
        label="Стоимость не выше, ₽", required=False, min_value=0,
        max_digits=12, decimal_places=2,
    )
    scope = forms.ChoiceField(
        label="Искать", required=False, initial="all", choices=[
            ("all", "По всем полям"), ("name", "Только по названию"),
        ],
    )
    hide_retired = forms.BooleanField(label="Скрыть списанные", required=False)
    needs_service = forms.BooleanField(
        label="Только требующие обслуживания", required=False,
    )
    sort = forms.ChoiceField(
        label="Сортировка", required=False, initial="name", choices=[
            ("name", "По названию"), ("price", "Сначала недорогие"),
            ("price_desc", "Сначала дорогие"),
            ("room", "По помещению и названию"),
            ("newest", "Сначала новые"),
        ],
    )
    page_size = forms.TypedChoiceField(
        label="На странице", required=False, initial=10, coerce=int,
        choices=[(2, "2"), (5, "5"), (10, "10"), (20, "20"), (50, "50")],
    )


class StatisticsForm(forms.Form):
    min_count = forms.IntegerField(
        label="Минимум устройств в помещении", required=False,
        min_value=0, max_value=1_000_000, initial=0,
    )
