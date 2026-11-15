from django import forms

from homepage.form_helpers import style_form
from rooms.models import Room


class RoomPhotoForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ("photo",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        image = getattr(photo, "image", None)
        if image is not None and image.format not in ("JPEG", "PNG", "WEBP"):
            raise forms.ValidationError("Разрешены только JPEG, PNG и WebP.")
        return photo
