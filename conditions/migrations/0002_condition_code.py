from django.db import migrations, models


LABELS = {
    "исправно": "working", "требует обслуживания": "service",
    "в ремонте": "repair", "списано": "retired",
}


def populate_codes(apps, schema_editor):
    Condition = apps.get_model("conditions", "Condition")
    for condition in Condition.objects.using(schema_editor.connection.alias).all():
        if condition.name not in LABELS:
            raise ValueError(f"Неизвестное состояние: {condition.name}")
        condition.code = LABELS[condition.name]
        condition.save(update_fields=["code"])


class Migration(migrations.Migration):
    dependencies = [("conditions", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="condition", name="code",
            field=models.CharField(max_length=12, null=True),
        ),
        migrations.RunPython(populate_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="condition", name="code",
            field=models.CharField(
                "Код состояния", max_length=12, unique=True,
                choices=[(code, label) for label, code in LABELS.items()],
                help_text="Постоянный код; название определяется автоматически.",
            ),
        ),
        migrations.AddConstraint(
            model_name="condition",
            constraint=models.CheckConstraint(
                condition=models.Q(code__in=(
                    "working", "service", "repair", "retired",
                )), name="known_condition_code",
            ),
        ),
    ]
