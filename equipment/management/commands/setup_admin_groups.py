from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


GROUPS = {
    "Наблюдатели техники": ("view",),
    "Операторы техники": ("view", "add", "change"),
}


class Command(BaseCommand):
    help = "Создать группы админки без назначения ролей пользователям"

    def handle(self, *args, **options):
        domain = Permission.objects.filter(content_type__app_label__in=(
            "equipment", "rooms", "conditions", "users",
        ))
        for name, operations in GROUPS.items():
            group, _ = Group.objects.get_or_create(name=name)
            ids = [permission.pk for permission in domain
                   if permission.codename.split("_", 1)[0] in operations]
            group.permissions.set(ids)
            self.stdout.write(f"{name}: {len(ids)} разрешений")
