from django import forms
from django.contrib import admin

from users.models import User


class ProjectUserForm(forms.ModelForm):
    new_password = forms.CharField(
        label="Новый пароль", required=False,
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = User
        fields = ("login",)

    def clean(self):
        data = super().clean() or {}
        if not self.instance.pk and not data.get("new_password"):
            self.add_error("new_password", "Укажите пароль пользователя.")
        return data


@admin.register(User)
class ProjectUserAdmin(admin.ModelAdmin):
    form = ProjectUserForm
    list_display = ("id", "login")
    search_fields = ("login",)
    ordering = ("login", "pk")
    list_per_page = 10

    def save_model(self, request, obj, form, change):
        password = form.cleaned_data.get("new_password")
        if password:
            obj.set_password(password)
        super().save_model(request, obj, form, change)
