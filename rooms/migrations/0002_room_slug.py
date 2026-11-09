from django.db import migrations, models
from django.utils.text import slugify
from unidecode import unidecode


def populate_slugs(apps, schema_editor):
    Room = apps.get_model("rooms", "Room")
    for room in Room.objects.using(schema_editor.connection.alias).order_by("pk"):
        base = slugify(unidecode(room.name))[:150].strip("-") or "room"
        room.slug = f"{base}-{room.pk}"
        room.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [("rooms", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="room", name="slug",
            field=models.SlugField(max_length=180, null=True, editable=False),
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="room", name="slug",
            field=models.SlugField(
                "URL-идентификатор", max_length=180, unique=True,
                blank=True, editable=False,
            ),
        ),
        migrations.AlterField(
            model_name="room", name="name",
            field=models.CharField(
                "Название", max_length=150, unique=True,
                help_text="Название помещения, в котором размещена техника.",
            ),
        ),
    ]
