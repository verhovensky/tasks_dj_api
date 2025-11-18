from io import StringIO

import pytest
from django.core.management import call_command

from tasks_api.users.models import User

pytestmark = pytest.mark.django_db


def test_create_user_with_email_and_password() -> None:
    """Тест создания обычного пользователя через UserManager."""
    user: User = User.objects.create_user(
        email="john@example.com",
        password="something-r@nd0m!",
    )

    assert user.email == "john@example.com"
    assert not user.is_staff
    assert not user.is_superuser
    assert user.check_password("something-r@nd0m!")
    assert user.username is None


def test_create_superuser_with_email_and_password() -> None:
    """Тест создания суперпользователя через UserManager."""
    user: User = User.objects.create_superuser(
        email="admin@example.com",
        password="something-r@nd0m!",
    )

    assert user.email == "admin@example.com"
    assert user.is_staff
    assert user.is_superuser
    assert user.username is None


def test_create_superuser_ignores_username() -> None:
    """Тест создания суперпользователя игнорирует username."""
    user: User = User.objects.create_superuser(
        email="test@example.com",
        password="something-r@nd0m!",
    )

    assert user.username is None


def test_createsuperuser_command_creates_superuser() -> None:
    """Тест команды createsuperuser работает с кастомным UserManager."""
    out = StringIO()
    command_result: str | None = call_command(
        "createsuperuser",
        "--email",
        "henry@example.com",
        interactive=False,
        stdout=out,
    )

    assert command_result is None
    assert out.getvalue() == "Superuser created successfully.\n"
    user: User = User.objects.get(email="henry@example.com")
    assert not user.has_usable_password()
