"""Учётные записи проекта; не заменяют встроенную модель администратора."""

from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class User(models.Model):
    login = models.CharField("Логин", max_length=150, unique=True)
    password = models.CharField("Хеш пароля", max_length=128)
    objects = models.Manager["User"]()

    class Meta:
        ordering = ["pk"]
        verbose_name = "пользователь проекта"
        verbose_name_plural = "пользователи проекта"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(login=""), name="user_login_not_empty",
            ),
        ]

    def set_password(self, raw_password: str) -> None:
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)

    def __str__(self) -> str:
        return self.login
