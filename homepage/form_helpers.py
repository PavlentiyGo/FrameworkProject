from django import forms


def style_form(form: forms.BaseForm) -> None:
    """Единое оформление полей; валидация остаётся на сервере Django."""
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.HiddenInput):
            continue
        if isinstance(widget, forms.CheckboxInput):
            css = "form-check-input"
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            css = "form-select"
        else:
            css = "form-control"
        widget.attrs["class"] = css
