"""Проверка параметров поиска, сортировки и пагинации ПР9."""

from django import forms
from django.utils import timezone

from conditions.models import Condition
from equipment.models import Device
from homepage.form_helpers import style_form
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)


class StatisticsForm(forms.Form):
    min_count = forms.IntegerField(
        label="Минимум устройств в помещении", required=False,
        min_value=0, max_value=1_000_000, initial=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)


class DeviceForm(forms.ModelForm):
    current_condition = forms.CharField(
        label="Состояние", disabled=True, required=False,
        help_text="Новая техника регистрируется исправной; списание отдельно.",
    )

    class Meta:
        model = Device
        fields = (
            "name", "device_type", "manufacturer", "model", "purchase_year",
            "price", "room", "service_interval", "notes",
        )
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
        help_texts = {
            "name": "Название должно быть уникальным в выбранном помещении.",
            "purchase_year": "От 1900 до текущего года включительно.",
            "notes": "Необязательное описание особенностей или обслуживания.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["current_condition"].initial = (
            self.instance.condition.name if self.instance.pk else "исправно"
        )
        if not self.instance.pk:
            self.fields["purchase_year"].initial = timezone.localdate().year
        style_form(self)

    def clean_name(self) -> str:
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 2:
            raise forms.ValidationError(
                "Название должно быть не короче 2 символов."
            )
        return name

    def clean_purchase_year(self) -> int:
        year = self.cleaned_data["purchase_year"]
        if not 1900 <= year <= timezone.localdate().year:
            raise forms.ValidationError(
                "Год покупки должен быть от 1900 до текущего."
            )
        return year

    def clean(self):
        data = super().clean() or {}
        room = data.get("room")
        name = data.get("name")
        if room and name:
            duplicates = Device.objects.filter(room=room, name__iexact=name)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(
                    "В этом помещении уже есть устройство с таким названием."
                )
        if self.instance.pk and room:
            retired = self.instance.condition.code == Condition.Code.RETIRED
            if retired and room.pk != self.instance.room_id:
                raise forms.ValidationError(
                    "Нельзя перемещать списанную технику в другое помещение."
                )
        return data
