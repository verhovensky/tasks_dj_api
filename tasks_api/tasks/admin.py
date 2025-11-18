from django.contrib import admin
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .enums import TaskPriority, TaskStatus
from .models import Comment, Tag, Task


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("content", "created_by", "created_at")
    readonly_fields = ("created_by", "created_at", "updated_at")
    can_delete = True

    def has_add_permission(self, request, obj=None):
        return True


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color_display", "task_count", "created_at", "created_by")
    list_filter = ("created_at",)
    search_fields = ("name",)
    readonly_fields = ("uuid", "created_at", "updated_at", "created_by", "updated_by")
    ordering = ("name",)

    fieldsets = (
        (None, {"fields": ("name", "color")}),
        (
            _("Metadata"),
            {
                "fields": (
                    "uuid",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                    "is_deleted",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Color Preview"))
    def color_display(self, obj):
        """Отобразить цвет в виде цветного блока."""
        if obj.color:
            return format_html(
                '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
                obj.color,
            )
        return "-"

    @admin.display(description=_("Tasks"))
    def task_count(self, obj):
        """Отобразить количество задач с этим тегом."""
        return obj.tasks.filter(is_deleted=False).count()

    def save_model(self, request, obj, form, change):
        """Установить created_by/updated_by при сохранении."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "task_link", "content_preview", "created_by", "created_at")
    list_filter = ("created_at", "task__status", "created_by")
    search_fields = ("content", "task__title", "created_by__email")
    readonly_fields = ("uuid", "created_at", "updated_at", "created_by", "updated_by")
    autocomplete_fields = ("task",)
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("task", "content")}),
        (
            _("Metadata"),
            {
                "fields": (
                    "uuid",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                    "is_deleted",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Task"))
    def task_link(self, obj):
        url = reverse("admin:tasks_task_change", args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)

    @admin.display(description=_("Content"))
    def content_preview(self, obj):
        """Отобразить укороченный контент."""
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content

    def save_model(self, request, obj, form, change):
        """Установить created_by/updated_by при сохранении."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Админ-интерфейс для Task с комплексной фильтрацией и inline комментариями."""

    list_display = (
        "id",
        "title",
        "status_badge",
        "priority_badge",
        "assigned_to",
        "due_date",
        "is_overdue_display",
        "comments_count",
        "created_by",
        "created_at",
    )
    list_filter = (
        "status",
        "priority",
        "is_deleted",
        "created_at",
        "due_date",
        ("assigned_to", admin.RelatedOnlyFieldListFilter),
        ("created_by", admin.RelatedOnlyFieldListFilter),
        ("tags", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("title", "description", "created_by__email", "assigned_to__email")
    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "is_overdue",
        "is_completed",
    )
    filter_horizontal = ("tags",)
    autocomplete_fields = ("assigned_to",)
    date_hierarchy = "created_at"
    inlines = [CommentInline]

    fieldsets = (
        (None, {"fields": ("title", "description", "status", "priority")}),
        (_("Assignment & Deadline"), {"fields": ("assigned_to", "due_date", "tags")}),
        (
            _("Status Information"),
            {"fields": ("is_overdue", "is_completed"), "classes": ("collapse",)},
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "uuid",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                    "is_deleted",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    actions = [
        "mark_as_completed",
        "mark_as_in_progress",
        "mark_as_todo",
        "soft_delete_selected",
    ]

    def get_queryset(self, request):
        """Оптимизировать queryset с помощью select_related и prefetch_related."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("created_by", "updated_by", "assigned_to").prefetch_related(
            "tags", "comments"
        )
        queryset = queryset.annotate(comments_count_annotation=Count("comments", filter=Q(comments__is_deleted=False)))
        return queryset

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        """Отобразить статус в виде цветного бейджа."""
        color_map = {
            TaskStatus.TODO: "#6c757d",  # Gray
            TaskStatus.IN_PROGRESS: "#0d6efd",  # Blue
            TaskStatus.COMPLETED: "#198754",  # Green
        }
        color = color_map.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description=_("Priority"))
    def priority_badge(self, obj):
        """Отобразить приоритет в виде цветного бейджа."""
        color_map = {
            TaskPriority.LOW: "#28a745",  # Green
            TaskPriority.MEDIUM: "#ffc107",  # Yellow
            TaskPriority.HIGH: "#fd7e14",  # Orange
            TaskPriority.CRITICAL: "#dc3545",  # Red
        }
        color = color_map.get(obj.priority, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display(),
        )

    @admin.display(description=_("Deadline Status"))
    def is_overdue_display(self, obj):
        """Отобразить статус просрочки с иконкой."""
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠ {}</span>', _("Overdue"))
        return format_html('<span style="color: green;">✓ {}</span>', _("On track"))

    @admin.display(description=_("Comments"), ordering="comments_count_annotation")
    def comments_count(self, obj):
        """Отобразить количество комментариев."""
        if hasattr(obj, "comments_count_annotation"):
            count = obj.comments_count_annotation
        else:
            count = obj.comments.filter(is_deleted=False).count()
        return format_html("<strong>{}</strong>", count)

    def save_model(self, request, obj, form, change):
        """Установить created_by/updated_by при сохранении."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """Установить created_by/updated_by для inline комментариев."""
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.created_by = request.user
            instance.updated_by = request.user
            instance.save()
        formset.save_m2m()

    # Админ-экшены
    @admin.action(description=_("Mark selected tasks as completed"))
    def mark_as_completed(self, request, queryset):
        """Отметить выбранные задачи как выполненные."""
        updated = queryset.update(status=TaskStatus.COMPLETED)
        self.message_user(request, _(f"{updated} task(s) marked as completed."))

    @admin.action(description=_("Mark selected tasks as in progress"))
    def mark_as_in_progress(self, request, queryset):
        """Отметить выбранные задачи как в процессе."""
        updated = queryset.update(status=TaskStatus.IN_PROGRESS)
        self.message_user(request, _(f"{updated} task(s) marked as in progress."))

    @admin.action(description=_("Mark selected tasks as todo"))
    def mark_as_todo(self, request, queryset):
        """Отметить выбранные задачи как todo."""
        updated = queryset.update(status=TaskStatus.TODO)
        self.message_user(request, _(f"{updated} task(s) marked as todo."))

    @admin.action(description=_("Soft delete selected tasks"))
    def soft_delete_selected(self, request, queryset):
        """Мягко удалить выбранные задачи."""
        updated = queryset.update(is_deleted=True)
        self.message_user(request, _(f"{updated} task(s) soft deleted."))
