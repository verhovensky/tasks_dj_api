from typing import NamedTuple

from tasks_api.tasks.models import Comment, Task
from tasks_api.tasks.tests.factories import CommentFactory, TaskFactory
from tasks_api.users.models import User
from tasks_api.users.tests.factories import UserFactory


class AssignedTaskContext(NamedTuple):
    task: Task
    creator: User
    assignee: User


class TaskWithCommentsContext(NamedTuple):
    task: Task
    creator: User
    comments: list[Comment]
    comment_authors: list[User]


class MultiUserTaskContext(NamedTuple):
    task: Task
    creator: User
    assignee: User
    other_user: User


def create_assigned_task(**kwargs) -> AssignedTaskContext:
    """
    Создать задачу с создателем и назначенным пользователем.

    Args:
        **kwargs: Переопределение значений по умолчанию для создания задачи (status, priority, и т.д.)

    Returns:
        AssignedTaskContext с task, creator и assignee
    """
    creator = UserFactory()
    assignee = UserFactory()

    task_defaults = {
        "created_by": creator,
        "updated_by": creator,
        "assigned_to": assignee,
    }
    task_defaults.update(kwargs)

    task = TaskFactory(**task_defaults)

    return AssignedTaskContext(task=task, creator=creator, assignee=assignee)


def create_task_with_comments(comments_count: int = 2, **task_kwargs) -> TaskWithCommentsContext:
    """
    Создать задачу с несколькими комментариями от разных пользователей.

    Args:
        comments_count: Количество комментариев для создания
        **task_kwargs: Переопределение значений по умолчанию для создания задачи

    Returns:
        TaskWithCommentsContext с task, creator, comments и comment_authors
    """
    creator = UserFactory()

    task_defaults = {
        "created_by": creator,
        "updated_by": creator,
    }
    task_defaults.update(task_kwargs)

    task = TaskFactory(**task_defaults)

    comments = []
    comment_authors = []

    for _ in range(comments_count):
        author = UserFactory()
        comment = CommentFactory(
            task=task,
            created_by=author,
            updated_by=author,
        )
        comments.append(comment)
        comment_authors.append(author)

    return TaskWithCommentsContext(
        task=task,
        creator=creator,
        comments=comments,
        comment_authors=comment_authors,
    )


def create_multi_user_task(**kwargs) -> MultiUserTaskContext:
    """
    Создать задачу с создателем, назначенным пользователем и несвязанным пользователем.

    Args:
        **kwargs: Переопределение значений по умолчанию для создания задачи

    Returns:
        MultiUserTaskContext с task, creator, assignee и other_user
    """
    creator = UserFactory()
    assignee = UserFactory()
    other_user = UserFactory()

    task_defaults = {
        "created_by": creator,
        "updated_by": creator,
        "assigned_to": assignee,
    }
    task_defaults.update(kwargs)

    task = TaskFactory(**task_defaults)

    return MultiUserTaskContext(
        task=task,
        creator=creator,
        assignee=assignee,
        other_user=other_user,
    )
