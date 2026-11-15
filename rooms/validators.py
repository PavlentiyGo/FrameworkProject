from django.core.exceptions import ValidationError


def validate_photo_size(value) -> None:
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("Фотография должна быть не больше 5 МБ.")
