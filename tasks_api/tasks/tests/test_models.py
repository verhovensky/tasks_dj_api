import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from tasks_api.tasks.enums import TaskPriority, TaskStatus
from tasks_api.tasks.models import Comment, Tag, Task
from tasks_api.tasks.tests.factories import CommentFactory, TagFactory, TaskFactory
from tasks_api.users.models import User
from tasks_api.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


# Tag Model Tests


def test_create_tag_with_valid_data_creates_tag(
    user: User,
    tag_name: str = "urgent",
    tag_color: str = "#FF0000",
) -> None:
    """Тест создания тега с валидными данными создает тег."""
    tag: Tag = TagFactory(
        name=tag_name,
        color=tag_color,
        created_by=user,
        updated_by=user,
    )

    assert tag.id is not None
    assert tag.name == tag_name
    assert tag.color == tag_color
    assert tag.created_by == user


@pytest.mark.parametrize(
    "color",
    [
        "#FF0000",
        "#00FF00",
        "#0000FF",
        "#ABCDEF",
        "#123456",
        "#ffffff",
    ],
)
def test_create_tag_with_valid_color_format_creates_tag(
    user: User,
    color: str,
    tag_name: str = "test",
) -> None:
    """Тест создания тега с валидным форматом цвета создает тег."""
    tag: Tag = TagFactory(name=tag_name, color=color, created_by=user, updated_by=user)

    assert tag.color == color


@pytest.mark.parametrize(
    "invalid_color",
    [
        "FF0000",
        "#FF00",
        "#FF00000",
        "#GGGGGG",
        "red",
    ],
)
def test_create_tag_with_invalid_color_format_raises_validation_error(
    user: User,
    invalid_color: str,
    tag_name: str = "test",
) -> None:
    """Тест создания тега с невалидным форматом цвета вызывает ValidationError."""
    tag: Tag = Tag(name=tag_name, color=invalid_color, created_by=user, updated_by=user)

    with pytest.raises(ValidationError) as exc_info:
        tag.full_clean()

    assert "color" in exc_info.value.error_dict


def test_create_tag_without_color_creates_tag(
    user: User,
    tag_name: str = "test",
) -> None:
    """Тест создания тега без цвета создает тег."""
    tag: Tag = TagFactory(name=tag_name, color=None, created_by=user, updated_by=user)

    assert tag.id is not None
    assert tag.color is None


def test_create_duplicate_tag_name_case_insensitive_raises_integrity_error(
    user: User,
    tag_name: str = "urgent",
) -> None:
    """Тест создания дубликата имени тега без учета регистра вызывает IntegrityError."""
    TagFactory(name=tag_name, created_by=user, updated_by=user)

    with pytest.raises(IntegrityError):
        Tag.objects.create(name=tag_name.upper(), created_by=user, updated_by=user)


def test_tag_str_returns_name(tag_name: str = "important") -> None:
    """Тест что __str__ тега возвращает имя."""
    tag: Tag = TagFactory(name=tag_name)

    assert str(tag) == tag_name


def test_tag_ordering_returns_alphabetical_by_name(
    user: User,
    tag_name_alpha: str = "alpha",
    tag_name_bravo: str = "bravo",
    tag_name_charlie: str = "charlie",
) -> None:
    """Тест что сортировка тегов возвращает алфавитный порядок по имени."""
    tag_c: Tag = TagFactory(name=tag_name_charlie, created_by=user, updated_by=user)
    tag_a: Tag = TagFactory(name=tag_name_alpha, created_by=user, updated_by=user)
    tag_b: Tag = TagFactory(name=tag_name_bravo, created_by=user, updated_by=user)

    tags: list[Tag] = list(Tag.objects.all())

    assert tags == [tag_a, tag_b, tag_c]


# Task Model Tests


def test_create_task_with_valid_data_creates_task(
    user: User,
    task_title: str = "Test Task",
    task_description: str = "Test Description",
) -> None:
    """Тест создания задачи с валидными данными создает задачу."""
    task: Task = TaskFactory(
        title=task_title,
        description=task_description,
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        created_by=user,
        updated_by=user,
    )

    assert task.id is not None
    assert task.title == task_title
    assert task.description == task_description
    assert task.status == TaskStatus.TODO
    assert task.priority == TaskPriority.HIGH


@pytest.mark.parametrize(
    "status",
    [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED],
)
def test_create_task_with_different_statuses_creates_task(user: User, status: str) -> None:
    """Тест создания задачи с разными статусами создает задачу."""
    task: Task = TaskFactory(status=status, created_by=user, updated_by=user)

    assert task.status == status


@pytest.mark.parametrize(
    "priority",
    [TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL],
)
def test_create_task_with_different_priorities_creates_task(user: User, priority: str) -> None:
    """Тест создания задачи с разными приоритетами создает задачу."""
    task: Task = TaskFactory(priority=priority, created_by=user, updated_by=user)

    assert task.priority == priority


def test_task_mark_completed_with_todo_status_changes_to_completed() -> None:
    """Тест что mark_completed меняет статус на COMPLETED."""
    task: Task = TaskFactory(status=TaskStatus.TODO)

    task.mark_completed()

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


def test_task_mark_in_progress_with_todo_status_changes_to_in_progress() -> None:
    """Тест что mark_in_progress меняет статус на IN_PROGRESS."""
    task: Task = TaskFactory(status=TaskStatus.TODO)

    task.mark_in_progress()

    task.refresh_from_db()
    assert task.status == TaskStatus.IN_PROGRESS


def test_task_mark_todo_with_completed_status_changes_to_todo() -> None:
    """Тест что mark_todo меняет статус на TODO."""
    task: Task = TaskFactory(status=TaskStatus.COMPLETED)

    task.mark_todo()

    task.refresh_from_db()
    assert task.status == TaskStatus.TODO


def test_task_assign_to_with_user_assigns_user() -> None:
    """Тест что assign_to назначает пользователя."""
    task: Task = TaskFactory(assigned_to=None)
    user: User = UserFactory()

    task.assign_to(user)

    task.refresh_from_db()
    assert task.assigned_to == user


def test_task_is_overdue_with_past_due_date_and_not_completed_returns_true(
    days_in_past: int = 1,
) -> None:
    """Тест что is_overdue возвращает True для просроченной незавершенной задачи."""
    past_date = timezone.now() - timezone.timedelta(days=days_in_past)
    task: Task = TaskFactory(due_date=past_date, status=TaskStatus.TODO)

    assert task.is_overdue is True


def test_task_is_overdue_with_future_due_date_returns_false(
    days_in_future: int = 1,
) -> None:
    """Тест что is_overdue возвращает False для будущей даты."""
    future_date = timezone.now() + timezone.timedelta(days=days_in_future)
    task: Task = TaskFactory(due_date=future_date, status=TaskStatus.TODO)

    assert task.is_overdue is False


def test_task_is_overdue_with_past_due_date_and_completed_returns_false(
    days_in_past: int = 1,
) -> None:
    """Тест что is_overdue возвращает False для просроченной завершенной задачи."""
    past_date = timezone.now() - timezone.timedelta(days=days_in_past)
    task: Task = TaskFactory(due_date=past_date, status=TaskStatus.COMPLETED)

    assert task.is_overdue is False


def test_task_is_overdue_with_no_due_date_returns_false() -> None:
    """Тест что is_overdue возвращает False когда нет due_date."""
    task: Task = TaskFactory(due_date=None, status=TaskStatus.TODO)

    assert task.is_overdue is False


def test_task_is_completed_with_completed_status_returns_true() -> None:
    """Тест что is_completed возвращает True для завершенной задачи."""
    task: Task = TaskFactory(status=TaskStatus.COMPLETED)

    assert task.is_completed is True


def test_task_is_completed_with_todo_status_returns_false() -> None:
    """Тест что is_completed возвращает False для незавершенной задачи."""
    task: Task = TaskFactory(status=TaskStatus.TODO)

    assert task.is_completed is False


def test_task_tags_many_to_many_adds_multiple_tags(
    expected_tags_count: int = 3,
) -> None:
    """Тест что можно добавить несколько тегов к задаче."""
    task: Task = TaskFactory()
    tag1: Tag = TagFactory()
    tag2: Tag = TagFactory()
    tag3: Tag = TagFactory()

    task.tags.add(tag1, tag2, tag3)

    assert task.tags.count() == expected_tags_count
    assert tag1 in task.tags.all()
    assert tag2 in task.tags.all()
    assert tag3 in task.tags.all()


def test_task_str_returns_title(task_title: str = "Important Task") -> None:
    """Тест что __str__ задачи возвращает название."""
    task: Task = TaskFactory(title=task_title)

    assert str(task) == task_title


def test_task_ordering_returns_newest_first(user: User) -> None:
    """Тест что сортировка задач возвращает новые первыми."""
    task1: Task = TaskFactory(created_by=user, updated_by=user)
    task2: Task = TaskFactory(created_by=user, updated_by=user)
    task3: Task = TaskFactory(created_by=user, updated_by=user)

    tasks: list[Task] = list(Task.objects.all())

    assert tasks == [task3, task2, task1]


# Comment Model Tests


def test_create_comment_with_valid_data_creates_comment(
    user: User,
    comment_content: str = "Great work!",
) -> None:
    """Тест создания комментария с валидными данными создает комментарий."""
    task: Task = TaskFactory()
    comment: Comment = CommentFactory(
        task=task,
        content=comment_content,
        created_by=user,
        updated_by=user,
    )

    assert comment.id is not None
    assert comment.task == task
    assert comment.content == comment_content
    assert comment.created_by == user


def test_comment_task_relationship_cascade_deletes_comments() -> None:
    """Тест что удаление задачи каскадно удаляет комментарии."""
    task: Task = TaskFactory()
    CommentFactory(task=task)
    CommentFactory(task=task)

    task_id: int = task.id
    task.delete()

    assert Comment.objects.filter(task_id=task_id).count() == 0


def test_comment_str_returns_formatted_string(
    task_title: str = "Test Task",
    user_name: str = "John Doe",
) -> None:
    """Тест что __str__ комментария возвращает форматированную строку."""
    task: Task = TaskFactory(title=task_title)
    user: User = UserFactory(name=user_name)
    comment: Comment = CommentFactory(task=task, created_by=user)

    comment_str: str = str(comment)

    assert task_title in comment_str
    assert user_name in comment_str


def test_comment_ordering_returns_oldest_first() -> None:
    """Тест что сортировка комментариев возвращает старые первыми."""
    task: Task = TaskFactory()
    comment1: Comment = CommentFactory(task=task)
    comment2: Comment = CommentFactory(task=task)
    comment3: Comment = CommentFactory(task=task)

    comments: list[Comment] = list(Comment.objects.all())

    assert comments == [comment1, comment2, comment3]


def test_task_comments_related_name_returns_comments(
    expected_comments_count: int = 2,
) -> None:
    """Тест что related_name 'comments' возвращает комментарии задачи."""
    task: Task = TaskFactory()
    comment1: Comment = CommentFactory(task=task)
    comment2: Comment = CommentFactory(task=task)
    other_task_comment: Comment = CommentFactory()

    task_comments: list[Comment] = list(task.comments.all())

    assert len(task_comments) == expected_comments_count
    assert comment1 in task_comments
    assert comment2 in task_comments
    assert other_task_comment not in task_comments
