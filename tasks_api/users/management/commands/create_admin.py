from django.conf import settings
from django.core.management.base import BaseCommand

from tasks_api.users.models import User


class Command(BaseCommand):
    help = "Создает суперпользователя"

    def handle(self, *args, **options):
        admin_email = "admin@admin.com"
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email=admin_email,
                password=settings.DEFAULT_ADMIN_PASSWORD,
                name="Admin",
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser created successfully with email: {admin_email}"))
        else:
            self.stdout.write(self.style.WARNING("Superuser already exists, skipping creation"))
