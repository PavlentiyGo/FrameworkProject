"""Проверка параметров GET перед передачей в SQL."""

from django import forms


class DeviceSearchForm(forms.Form):
    q = forms.CharField(
        label="Название, тип или производитель", required=False,
        max_length=150,
    )
    room_id = forms.ChoiceField(label="Помещение", required=False)
    condition = forms.ChoiceField(label="Состояние", required=False)
    max_price = forms.DecimalField(
        label="Стоимость не выше, ₽", required=False, min_value=0,
        max_digits=12, decimal_places=2,
    )


class StatisticsForm(forms.Form):
    min_count = forms.IntegerField(
        label="Минимум устройств в помещении", required=False,
        min_value=0, max_value=1_000_000, initial=0,
    )
