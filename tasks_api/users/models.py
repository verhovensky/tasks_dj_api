from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, EmailField
from django.utils.translation import gettext_lazy as _

from tasks_api.users.managers import UserManager


class User(AbstractUser):
    """
    Кастомная модель пользователя для Tasks API.
    Использует email в качестве идентификатора вместо username.
    """

    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def __str__(self) -> str:
        """Строковое представление пользователя для админки.

        Returns:
            str: ID пользователя, имя и email.

        """
        if self.name:
            return f"#{self.id} - {self.name} ({self.email})"
        return f"#{self.id} - {self.email}"
