from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tasks_api.tasks.enums import TaskPriority, TaskStatus
from tasks_api.tasks.models import Task
from tasks_api.tasks.tests.factories import TagFactory, TaskFactory
from tasks_api.tasks.tests.fixtures import create_assigned_task, create_multi_user_task
from tasks_api.users.models import User
from tasks_api.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


# Task list Tests


def test_list_tasks_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
) -> None:
    """Тест получения списка задач неаутентифицированным пользователем возвращает 401."""
    response = api_client.get(tasks_list_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_tasks_authenticated_user_returns_ok(
    authenticated_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
    batch_size: int = 3,
) -> None:
    """Тест получения списка задач аутентифицированным пользователем возвращает 200."""
    TaskFactory.create_batch(batch_size)

    response = authenticated_client.get(tasks_list_url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == batch_size


def test_list_tasks_excludes_deleted_tasks_returns_only_active(
    authenticated_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
) -> None:
    """Тест получения списка задач исключает удаленные задачи."""
    active_task: Task = TaskFactory()
    deleted_task: Task = TaskFactory(is_deleted=True)

    response = authenticated_client.get(tasks_list_url)

    task_ids: list[int] = [t["id"] for t in response.data["results"]]
    assert active_task.id in task_ids
    assert deleted_task.id not in task_ids


# Task Create Tests


def test_create_task_authenticated_user_valid_data_returns_created(
    authenticated_client: APIClient,
    user: User,
    tasks_list_url: str = "/api/tasks/",
    task_title: str = "New Task",
    task_description: str = "Task description",
) -> None:
    """Тест создания задачи аутентифицированным пользователем с валидными данными возвращает 201."""
    payload: dict[str, Any] = {
        "title": task_title,
        "description": task_description,
        "priority": TaskPriority.HIGH,
    }

    response = authenticated_client.post(tasks_list_url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == task_title
    assert response.data["description"] == task_description
    assert response.data["priority"] == TaskPriority.HIGH
    assert response.data["created_by"]["id"] == user.id


def test_create_task_with_tags_valid_tag_ids_returns_created(
    authenticated_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
    task_title: str = "New Task",
    expected_tags_count: int = 2,
) -> None:
    """Тест создания задачи с тегами возвращает 201."""
    tag1 = TagFactory()
    tag2 = TagFactory()
    payload: dict[str, Any] = {
        "title": task_title,
        "tag_ids": [tag1.id, tag2.id],
    }

    response = authenticated_client.post(tasks_list_url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data["tags"]) == expected_tags_count
    tag_ids: list[int] = [t["id"] for t in response.data["tags"]]
    assert tag1.id in tag_ids
    assert tag2.id in tag_ids


def test_create_task_with_single_tag_returns_created(
    authenticated_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
    task_title: str = "Task with Single Tag",
    task_description: str = "This task has one tag",
    expected_tags_count: int = 1,
) -> None:
    """Тест создания задачи с одним тегом возвращает 201 и правильно назначает тег."""
    tag = TagFactory()
    payload: dict[str, Any] = {
        "title": task_title,
        "description": task_description,
        "tag_ids": [tag.id],
    }

    response = authenticated_client.post(tasks_list_url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data["tags"]) == expected_tags_count
    assert response.data["tags"][0]["id"] == tag.id
    assert response.data["tags"][0]["name"] == tag.name

    url_check: str = reverse("api:task-detail", kwargs={"pk": response.data["id"]})
    response_check = authenticated_client.get(url_check)
    assert response_check.status_code == status.HTTP_200_OK
    assert len(response_check.data["tags"]) == expected_tags_count
    assert response_check.data["tags"][0]["id"] == tag.id
    assert response_check.data["tags"][0]["name"] == tag.name


def test_create_task_with_nonexistent_tag_ids_returns_bad_request(
    authenticated_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
    task_title: str = "Task with Invalid Tags",
    nonexistent_tag_id_1: int = 99999,
    nonexistent_tag_id_2: int = 88888,
) -> None:
    """Тест создания задачи с несуществующими tag_ids возвращает 400."""
    payload: dict[str, Any] = {
        "title": task_title,
        "tag_ids": [nonexistent_tag_id_1, nonexistent_tag_id_2],
    }

    response = authenticated_client.post(tasks_list_url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "tag_ids" in response.data


def test_create_task_missing_required_title_returns_bad_request(
    authenticated_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
    task_description: str = "Task description",
) -> None:
    """Тест создания задачи без обязательного поля title возвращает 400."""
    payload: dict[str, str] = {
        "description": task_description,
    }

    response = authenticated_client.post(tasks_list_url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "title" in response.data


def test_create_task_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
    task_title: str = "New Task",
) -> None:
    """Тест создания задачи неаутентифицированным пользователем возвращает 401."""
    payload: dict[str, str] = {"title": task_title}

    response = api_client.post(tasks_list_url, payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_task_authenticated_user_returns_ok(
    authenticated_client: APIClient,
    task: Task,
) -> None:
    """Тест получения детальной информации о задаче возвращает 200."""
    url: str = reverse("api:task-detail", kwargs={"pk": task.pk})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == task.id
    assert response.data["title"] == task.title
    assert "comments" in response.data


def test_retrieve_task_nonexistent_id_returns_not_found(
    authenticated_client: APIClient,
    nonexistent_id: int = 99999,
) -> None:
    """Тест получения несуществующей задачи возвращает 404."""
    url: str = reverse("api:task-detail", kwargs={"pk": nonexistent_id})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_retrieve_task_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    task: Task,
) -> None:
    """Тест получения задачи неаутентифицированным пользователем возвращает 401."""
    url: str = reverse("api:task-detail", kwargs={"pk": task.pk})

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Task Update Tests


def test_update_task_creator_valid_data_returns_ok(
    authenticated_client: APIClient,
    user: User,
    updated_title: str = "Updated Task",
    updated_description: str = "Updated description",
) -> None:
    """Тест обновления задачи создателем с валидными данными возвращает 200."""
    task: Task = TaskFactory(created_by=user, updated_by=user)
    url: str = reverse("api:task-detail", kwargs={"pk": task.pk})
    payload: dict[str, Any] = {
        "title": updated_title,
        "description": updated_description,
        "priority": TaskPriority.CRITICAL,
    }

    response = authenticated_client.put(url, payload)

    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.title == updated_title
    assert task.description == updated_description
    assert int(task.priority) == TaskPriority.CRITICAL.value


def test_partial_update_task_creator_valid_data_returns_ok(
    authenticated_client: APIClient,
    user: User,
    updated_title: str = "Updated Task",
) -> None:
    """Тест частичного обновления задачи создателем возвращает 200."""
    task: Task = TaskFactory(created_by=user, updated_by=user)
    url: str = reverse("api:task-detail", kwargs={"pk": task.pk})
    payload: dict[str, str] = {"title": updated_title}

    response = authenticated_client.patch(url, payload)

    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.title == updated_title


def test_update_task_non_creator_returns_forbidden(
    authenticated_client: APIClient,
    updated_title: str = "Updated Task",
) -> None:
    """Тест обновления задачи не создателем возвращает 403."""
    other_user: User = UserFactory()
    task: Task = TaskFactory(created_by=other_user, updated_by=other_user)
    url: str = reverse("api:task-detail", kwargs={"pk": task.pk})
    payload: dict[str, str] = {"title": updated_title}

    response = authenticated_client.put(url, payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN


# Task Delete Tests


def test_delete_task_creator_returns_no_content(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест удаления задачи создателем возвращает 204."""
    task: Task = TaskFactory(created_by=user, updated_by=user)
    url: str = reverse("api:task-detail", kwargs={"pk": task.pk})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    task.refresh_from_db()
    assert task.is_deleted is True


def test_delete_task_non_creator_returns_forbidden(
    authenticated_client: APIClient,
) -> None:
    """Тест удаления задачи не создателем возвращает 403."""
    other_user: User = UserFactory()
    task: Task = TaskFactory(created_by=other_user, updated_by=other_user)
    url: str = reverse("api:task-detail", kwargs={"pk": task.pk})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


# Task Custom Actions Tests


def test_assign_task_creator_valid_user_id_returns_ok(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест назначения задачи создателем с валидным user_id возвращает 200."""
    task: Task = TaskFactory(created_by=user, updated_by=user, assigned_to=None)
    assignee: User = UserFactory()
    url: str = reverse("api:task-assign", kwargs={"pk": task.pk})
    payload: dict[str, int] = {"user_id": assignee.id}

    response = authenticated_client.post(url, payload)

    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.assigned_to == assignee


def test_assign_task_non_creator_returns_forbidden(
    authenticated_client: APIClient,
) -> None:
    """Тест назначения задачи не создателем возвращает 403."""
    other_user: User = UserFactory()
    task: Task = TaskFactory(created_by=other_user, updated_by=other_user)
    assignee: User = UserFactory()
    url: str = reverse("api:task-assign", kwargs={"pk": task.pk})
    payload: dict[str, int] = {"user_id": assignee.id}

    response = authenticated_client.post(url, payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_complete_task_creator_todo_status_returns_ok(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест завершения задачи создателем возвращает 200 и меняет статус."""
    task: Task = TaskFactory(
        created_by=user,
        updated_by=user,
        status=TaskStatus.TODO,
    )
    url: str = reverse("api:task-complete", kwargs={"pk": task.pk})

    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


def test_mark_in_progress_task_creator_todo_status_returns_ok(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест изменения статуса задачи на IN_PROGRESS создателем возвращает 200."""
    task: Task = TaskFactory(
        created_by=user,
        updated_by=user,
        status=TaskStatus.TODO,
    )
    url: str = reverse("api:task-mark-in-progress", kwargs={"pk": task.pk})

    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.status == TaskStatus.IN_PROGRESS


def test_my_tasks_authenticated_user_returns_only_created_by_user(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест получения моих задач возвращает только задачи созданные пользователем."""
    my_task1: Task = TaskFactory(created_by=user, updated_by=user)
    my_task2: Task = TaskFactory(created_by=user, updated_by=user)
    other_task: Task = TaskFactory()
    url: str = reverse("api:task-my-tasks")

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    task_ids: list[int] = [t["id"] for t in response.data["results"]]
    assert my_task1.id in task_ids
    assert my_task2.id in task_ids
    assert other_task.id not in task_ids


def test_assigned_to_me_authenticated_user_returns_only_assigned_tasks(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест получения задач назначенных мне возвращает только назначенные задачи."""
    assigned_task1: Task = TaskFactory(assigned_to=user)
    assigned_task2: Task = TaskFactory(assigned_to=user)
    not_assigned_task: Task = TaskFactory(assigned_to=None)
    url: str = reverse("api:task-assigned-to-me")

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    task_ids: list[int] = [t["id"] for t in response.data["results"]]
    assert assigned_task1.id in task_ids
    assert assigned_task2.id in task_ids
    assert not_assigned_task.id not in task_ids


# Task Filtering Tests


@pytest.mark.parametrize(
    "filter_status",
    [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED],
)
def test_filter_tasks_by_status_returns_filtered_results(
    authenticated_client: APIClient,
    user: User,
    filter_status: str,
    tasks_list_url: str = "/api/tasks/",
) -> None:
    """Тест фильтрации задач по статусу возвращает отфильтрованные результаты."""
    matching_task: Task = TaskFactory(status=filter_status, created_by=user, updated_by=user)
    non_matching_task: Task = TaskFactory(status=TaskStatus.TODO, created_by=user, updated_by=user)

    response = authenticated_client.get(tasks_list_url, {"status": filter_status})

    assert response.status_code == status.HTTP_200_OK
    task_ids: list[int] = [t["id"] for t in response.data["results"]]
    assert matching_task.id in task_ids
    if filter_status != TaskStatus.TODO:
        assert non_matching_task.id not in task_ids


@pytest.mark.parametrize(
    "filter_priority",
    [TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL],
)
def test_filter_tasks_by_priority_returns_filtered_results(
    authenticated_client: APIClient,
    user: User,
    filter_priority: int,
    tasks_list_url: str = "/api/tasks/",
) -> None:
    """Тест фильтрации задач по приоритету возвращает отфильтрованные результаты."""
    matching_task: Task = TaskFactory(priority=filter_priority, created_by=user, updated_by=user)
    non_matching_task: Task = TaskFactory(priority=TaskPriority.LOW, created_by=user, updated_by=user)

    response = authenticated_client.get(tasks_list_url, {"priority": filter_priority})

    assert response.status_code == status.HTTP_200_OK
    task_ids: list[int] = [t["id"] for t in response.data["results"]]
    assert matching_task.id in task_ids
    if filter_priority != TaskPriority.LOW:
        assert non_matching_task.id not in task_ids


def test_filter_tasks_by_assigned_to_returns_filtered_results(
    authenticated_client: APIClient,
    user: User,
    tasks_list_url: str = "/api/tasks/",
) -> None:
    """Тест фильтрации задач по назначенному пользователю возвращает отфильтрованные результаты."""
    assignee: User = UserFactory()
    matching_task: Task = TaskFactory(assigned_to=assignee)
    non_matching_task: Task = TaskFactory(assigned_to=user)

    response = authenticated_client.get(tasks_list_url, {"assigned_to": assignee.id})

    assert response.status_code == status.HTTP_200_OK
    task_ids: list[int] = [t["id"] for t in response.data["results"]]
    assert matching_task.id in task_ids
    assert non_matching_task.id not in task_ids


def test_filter_tasks_by_tags_returns_filtered_results(
    authenticated_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
) -> None:
    """Тест фильтрации задач по тегам возвращает отфильтрованные результаты."""
    tag = TagFactory()
    matching_task: Task = TaskFactory()
    matching_task.tags.add(tag)
    non_matching_task: Task = TaskFactory()

    response = authenticated_client.get(tasks_list_url, {"tags": tag.id})

    assert response.status_code == status.HTTP_200_OK
    task_ids: list[int] = [t["id"] for t in response.data["results"]]
    assert matching_task.id in task_ids
    assert non_matching_task.id not in task_ids


# Task Search Tests


def test_search_tasks_by_title_returns_matching_results(
    authenticated_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
    search_term: str = "important",
) -> None:
    """Тест поиска задач по названию возвращает совпадающие результаты."""
    matching_task: Task = TaskFactory(title=f"This is {search_term} task")
    non_matching_task: Task = TaskFactory(title="Regular task")

    response = authenticated_client.get(tasks_list_url, {"search": search_term})

    assert response.status_code == status.HTTP_200_OK
    task_ids: list[int] = [t["id"] for t in response.data["results"]]
    assert matching_task.id in task_ids
    assert non_matching_task.id not in task_ids


def test_search_tasks_by_description_returns_matching_results(
    authenticated_client: APIClient,
    tasks_list_url: str = "/api/tasks/",
    search_term: str = "urgent",
) -> None:
    """Тест поиска задач по описанию возвращает совпадающие результаты."""
    matching_task: Task = TaskFactory(description=f"This is {search_term} description")
    non_matching_task: Task = TaskFactory(description="Regular description")

    response = authenticated_client.get(tasks_list_url, {"search": search_term})

    assert response.status_code == status.HTTP_200_OK
    task_ids: list[int] = [t["id"] for t in response.data["results"]]
    assert matching_task.id in task_ids
    assert non_matching_task.id not in task_ids


# Task Ordering Tests


@pytest.mark.parametrize(
    "ordering_field,expected_first_index",
    [
        ("created_at", 0),
        ("-created_at", 2),
        ("priority", 0),
        ("-priority", 2),
    ],
)
def test_order_tasks_by_field_returns_ordered_results(
    authenticated_client: APIClient,
    user: User,
    ordering_field: str,
    expected_first_index: int,
    tasks_list_url: str = "/api/tasks/",
) -> None:
    """Тест сортировки задач по полю возвращает отсортированные результаты."""
    task1: Task = TaskFactory(priority=TaskPriority.LOW, created_by=user, updated_by=user)
    task2: Task = TaskFactory(priority=TaskPriority.MEDIUM, created_by=user, updated_by=user)
    task3: Task = TaskFactory(priority=TaskPriority.HIGH, created_by=user, updated_by=user)
    tasks_list: list[Task] = [task1, task2, task3]

    response = authenticated_client.get(tasks_list_url, {"ordering": ordering_field})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["id"] == tasks_list[expected_first_index].id


# Permission Tests - Status Change


def test_complete_task_assignee_returns_forbidden(api_client: APIClient) -> None:
    """Тест завершения задачи назначенным пользователем возвращает 403."""
    context = create_assigned_task(status=TaskStatus.IN_PROGRESS)
    api_client.force_authenticate(user=context.assignee)
    url: str = reverse("api:task-complete", kwargs={"pk": context.task.pk})

    response = api_client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    context.task.refresh_from_db()
    assert context.task.status == TaskStatus.IN_PROGRESS


def test_mark_in_progress_task_assignee_returns_forbidden(
    api_client: APIClient,
) -> None:
    """Тест изменения статуса задачи на IN_PROGRESS назначенным пользователем возвращает 403."""
    context = create_assigned_task(status=TaskStatus.TODO)
    api_client.force_authenticate(user=context.assignee)
    url: str = reverse("api:task-mark-in-progress", kwargs={"pk": context.task.pk})

    response = api_client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    context.task.refresh_from_db()
    assert context.task.status == TaskStatus.TODO


def test_complete_task_other_user_returns_forbidden(api_client: APIClient) -> None:
    """Тест завершения задачи несвязанным пользователем возвращает 403."""
    context = create_multi_user_task(status=TaskStatus.IN_PROGRESS)
    api_client.force_authenticate(user=context.other_user)
    url: str = reverse("api:task-complete", kwargs={"pk": context.task.pk})

    response = api_client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    context.task.refresh_from_db()
    assert context.task.status == TaskStatus.IN_PROGRESS


def test_mark_in_progress_task_other_user_returns_forbidden(
    api_client: APIClient,
) -> None:
    """Тест изменения статуса на IN_PROGRESS несвязанным пользователем возвращает 403."""
    context = create_multi_user_task(status=TaskStatus.TODO)
    api_client.force_authenticate(user=context.other_user)
    url: str = reverse("api:task-mark-in-progress", kwargs={"pk": context.task.pk})

    response = api_client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    context.task.refresh_from_db()
    assert context.task.status == TaskStatus.TODO


# Permission Tests - Task Assignment


def test_assign_task_other_user_returns_forbidden(api_client: APIClient) -> None:
    """Тест назначения задачи несвязанным пользователем возвращает 403."""
    context = create_multi_user_task()
    new_assignee: User = UserFactory()
    api_client.force_authenticate(user=context.other_user)
    url: str = reverse("api:task-assign", kwargs={"pk": context.task.pk})

    response = api_client.post(url, {"user_id": new_assignee.id})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    context.task.refresh_from_db()
    assert context.task.assigned_to == context.assignee


def test_assign_task_inactive_user_returns_bad_request(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест назначения задачи неактивному пользователю возвращает 400."""
    task: Task = TaskFactory(created_by=user, updated_by=user)
    inactive_user: User = UserFactory(is_active=False)
    url: str = reverse("api:task-assign", kwargs={"pk": task.pk})

    response = authenticated_client.post(url, {"user_id": inactive_user.id})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "user_id" in response.data or "assigned_to" in response.data


def test_assign_task_nonexistent_user_returns_bad_request(
    authenticated_client: APIClient,
    user: User,
    nonexistent_user_id: int = 99999,
) -> None:
    """Тест назначения задачи несуществующему пользователю возвращает 400."""
    task: Task = TaskFactory(created_by=user, updated_by=user)
    url: str = reverse("api:task-assign", kwargs={"pk": task.pk})

    response = authenticated_client.post(url, {"user_id": nonexistent_user_id})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# Permission Tests - Task Update/Delete


def test_update_task_assignee_returns_forbidden(api_client: APIClient, updated_title: str = "Updated") -> None:
    """Тест обновления задачи назначенным пользователем возвращает 403."""
    context = create_assigned_task()
    api_client.force_authenticate(user=context.assignee)
    url: str = reverse("api:task-detail", kwargs={"pk": context.task.pk})

    response = api_client.patch(url, {"title": updated_title})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    context.task.refresh_from_db()
    assert context.task.title != updated_title


def test_delete_task_assignee_returns_forbidden(api_client: APIClient) -> None:
    """Тест удаления задачи назначенным пользователем возвращает 403."""
    context = create_assigned_task()
    api_client.force_authenticate(user=context.assignee)
    url: str = reverse("api:task-detail", kwargs={"pk": context.task.pk})

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    context.task.refresh_from_db()
    assert context.task.is_deleted is False


def test_delete_task_other_user_returns_forbidden(api_client: APIClient) -> None:
    """Тест удаления задачи несвязанным пользователем возвращает 403."""
    context = create_multi_user_task()
    api_client.force_authenticate(user=context.other_user)
    url: str = reverse("api:task-detail", kwargs={"pk": context.task.pk})

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    context.task.refresh_from_db()
    assert context.task.is_deleted is False


# Inactive User Tests


def test_create_task_inactive_user_returns_forbidden(
    api_client: APIClient,
    task_title: str = "New Task",
) -> None:
    """Тест создания задачи неактивным пользователем возвращает 403."""
    inactive_user: User = UserFactory(is_active=False)
    api_client.force_authenticate(user=inactive_user)
    url: str = "/api/tasks/"

    response = api_client.post(url, {"title": task_title})

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_tasks_inactive_user_returns_forbidden(api_client: APIClient) -> None:
    """Тест получения списка задач неактивным пользователем возвращает 403."""
    inactive_user: User = UserFactory(is_active=False)
    api_client.force_authenticate(user=inactive_user)
    url: str = "/api/tasks/"

    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
