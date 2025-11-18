from django.core.validators import RegexValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from tasks_api.utils.constants import (
    DEFAULT_MAX_CHAR_FIELD_LENGTH,
    MAX_TAG_COLOR_LENGTH,
    MAX_TAG_LENGTH,
    MAX_TASKS_STATUS_LENGTH,
    TAG_COLOR_REGEX,
)
from tasks_api.utils.models import BaseModel

from .enums import TaskPriority, TaskStatus


class Tag(BaseModel):
    """
    Модель тега для категоризации задач.

    Атрибуты:
        name: Уникальное название тега (максимум 15 символов, уникальность без учета регистра)
        color: Опциональный hex-код цвета для отображения в UI (например, #FF5733)
    """

    name = models.CharField(_("Tag Name"), max_length=MAX_TAG_LENGTH)
    color = models.CharField(
        _("Color"),
        max_length=MAX_TAG_COLOR_LENGTH,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=TAG_COLOR_REGEX,
                message=_("Color must be a valid hex code (e.g., #FF5733)"),
            )
        ],
        help_text=_("Hex color code for the tag (e.g., #FF5733)"),
    )

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        ordering = ["name"]
        constraints = [
            UniqueConstraint(
                Lower("name"),
                name="unique_tag_name_case_insensitive",
            ),
        ]

    def __str__(self):
        return self.name


class Task(BaseModel):
    """
    Модель задачи для управления пользовательскими задачами.

    Атрибуты:
        title: Название задачи (обязательно)
        description: Детальное описание задачи (опционально)
        status: Текущий статус задачи (TODO, IN_PROGRESS, COMPLETED)
        priority: Уровень приоритета задачи (LOW, MEDIUM, HIGH, CRITICAL)
        due_date: Опциональный дедлайн для завершения задачи
        assigned_to: Пользователь, которому назначена задача (опционально)
        tags: Many-to-many связь с моделью Tag
    """

    title = models.CharField(_("Title"), max_length=DEFAULT_MAX_CHAR_FIELD_LENGTH)
    description = models.TextField(_("Description"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=MAX_TASKS_STATUS_LENGTH,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )
    priority = models.IntegerField(
        _("Priority"),
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
    )
    due_date = models.DateTimeField(_("Due Date"), null=True, blank=True)
    assigned_to = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name=_("Assigned To"),
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="tasks",
        verbose_name=_("Tags"),
    )

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["priority", "-created_at"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return self.title

    def mark_completed(self):
        """Отметить задачу как выполненную."""
        self.status = TaskStatus.COMPLETED
        self.save(update_fields=["status", "updated_at"])

    def mark_in_progress(self):
        """Отметить задачу как выполняющуюся."""
        self.status = TaskStatus.IN_PROGRESS
        self.save(update_fields=["status", "updated_at"])

    def mark_todo(self):
        """Отметить задачу как невыполненную (todo)."""
        self.status = TaskStatus.TODO
        self.save(update_fields=["status", "updated_at"])

    def assign_to(self, user):
        """
        Назначить задачу конкретному пользователю.

        Args:
            user: Экземпляр User, которому назначается задача
        """
        self.assigned_to = user
        self.save(update_fields=["assigned_to", "updated_at"])

    @property
    def is_overdue(self):
        """
        Проверить, просрочена ли задача.

        Сравнение происходит в UTC timezone-aware формате.
        """
        if self.due_date and self.status != TaskStatus.COMPLETED:
            return timezone.now() > self.due_date
        return False

    @property
    def is_completed(self):
        """Проверить, выполнена ли задача."""
        return self.status == TaskStatus.COMPLETED


class Comment(BaseModel):
    """
    Модель комментария для обсуждения задач.

    Атрибуты:
        task: Ссылка на задачу, к которой относится комментарий
        content: Текстовое содержимое комментария
    """

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Task"),
    )
    content = models.TextField(_("Content"))

    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["task", "created_at"]),
        ]

    def __str__(self) -> str:
        if self.created_by:
            author = self.created_by.name or self.created_by.email
        else:
            author = "Unknown"
        return f"Comment on {self.task.title} by {author}"
