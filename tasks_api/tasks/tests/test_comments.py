from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tasks_api.tasks.models import Comment, Task
from tasks_api.tasks.tests.factories import CommentFactory, TaskFactory
from tasks_api.tasks.tests.fixtures import create_task_with_comments
from tasks_api.users.models import User
from tasks_api.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


# Comment list Tests


def test_list_comments_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    comments_list_url: str = "/api/comments/",
) -> None:
    """Тест получения списка комментариев неаутентифицированным пользователем возвращает 401."""
    response = api_client.get(comments_list_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_comments_authenticated_user_returns_ok(
    authenticated_client: APIClient,
    comments_list_url: str = "/api/comments/",
    batch_size: int = 3,
) -> None:
    """Тест получения списка комментариев аутентифицированным пользователем возвращает 200."""
    CommentFactory.create_batch(batch_size)

    response = authenticated_client.get(comments_list_url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == batch_size


def test_list_comments_excludes_deleted_comments_returns_only_active(
    authenticated_client: APIClient,
    comments_list_url: str = "/api/comments/",
) -> None:
    """Тест получения списка комментариев исключает удаленные комментарии."""
    active_comment: Comment = CommentFactory()
    deleted_comment: Comment = CommentFactory(is_deleted=True)

    response = authenticated_client.get(comments_list_url)

    comment_ids: list[int] = [comment["id"] for comment in response.data["results"]]
    assert active_comment.id in comment_ids
    assert deleted_comment.id not in comment_ids


# Comment Create Tests


def test_create_comment_authenticated_user_valid_data_returns_created(
    authenticated_client: APIClient,
    user: User,
    task: Task,
    comments_list_url: str = "/api/comments/",
    comment_content: str = "Great work!",
) -> None:
    """Тест создания комментария аутентифицированным пользователем с валидными данными возвращает 201."""
    payload: dict[str, Any] = {
        "task": task.id,
        "content": comment_content,
    }

    response = authenticated_client.post(comments_list_url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == comment_content
    assert response.data["task"] == task.id
    assert response.data["author"]["id"] == user.id


def test_create_comment_missing_required_content_returns_bad_request(
    authenticated_client: APIClient,
    task: Task,
    comments_list_url: str = "/api/comments/",
) -> None:
    """Тест создания комментария без обязательного поля content возвращает 400."""
    payload: dict[str, int] = {
        "task": task.id,
    }

    response = authenticated_client.post(comments_list_url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "content" in response.data


def test_create_comment_missing_required_task_returns_bad_request(
    authenticated_client: APIClient,
    comments_list_url: str = "/api/comments/",
    comment_content: str = "Great work!",
) -> None:
    """Тест создания комментария без обязательного поля task возвращает 400."""
    payload: dict[str, str] = {
        "content": comment_content,
    }

    response = authenticated_client.post(comments_list_url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "task" in response.data


def test_create_comment_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    task: Task,
    comments_list_url: str = "/api/comments/",
    comment_content: str = "Great work!",
) -> None:
    """Тест создания комментария неаутентифицированным пользователем возвращает 401."""
    payload: dict[str, Any] = {
        "task": task.id,
        "content": comment_content,
    }

    response = api_client.post(comments_list_url, payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Comment Retrieve Tests


def test_retrieve_comment_authenticated_user_returns_ok(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест получения детальной информации о комментарии возвращает 200."""
    comment: Comment = CommentFactory(created_by=user, updated_by=user)
    url: str = reverse("api:comment-detail", kwargs={"pk": comment.pk})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == comment.id
    assert response.data["content"] == comment.content


def test_retrieve_comment_nonexistent_id_returns_not_found(
    authenticated_client: APIClient,
    nonexistent_id: int = 99999,
) -> None:
    """Тест получения несуществующего комментария возвращает 404."""
    url: str = reverse("api:comment-detail", kwargs={"pk": nonexistent_id})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_retrieve_comment_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    user: User,
) -> None:
    """Тест получения комментария неаутентифицированным пользователем возвращает 401."""
    comment: Comment = CommentFactory(created_by=user, updated_by=user)
    url: str = reverse("api:comment-detail", kwargs={"pk": comment.pk})

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Comment Update Tests


def test_update_comment_creator_valid_data_returns_ok(
    authenticated_client: APIClient,
    user: User,
    task: Task,
    updated_content: str = "Updated comment content",
) -> None:
    """Тест обновления комментария создателем с валидными данными возвращает 200."""
    comment: Comment = CommentFactory(created_by=user, updated_by=user)
    url: str = reverse("api:comment-detail", kwargs={"pk": comment.pk})
    payload: dict[str, Any] = {
        "task": task.id,
        "content": updated_content,
    }

    response = authenticated_client.put(url, payload)

    assert response.status_code == status.HTTP_200_OK
    comment.refresh_from_db()
    assert comment.content == updated_content


def test_partial_update_comment_creator_valid_data_returns_ok(
    authenticated_client: APIClient,
    user: User,
    updated_content: str = "Updated comment content",
) -> None:
    """Тест частичного обновления комментария создателем возвращает 200."""
    comment: Comment = CommentFactory(created_by=user, updated_by=user)
    url: str = reverse("api:comment-detail", kwargs={"pk": comment.pk})
    payload: dict[str, str] = {"content": updated_content}

    response = authenticated_client.patch(url, payload)

    assert response.status_code == status.HTTP_200_OK
    comment.refresh_from_db()
    assert comment.content == updated_content


def test_update_comment_non_creator_returns_forbidden(
    authenticated_client: APIClient,
    task: Task,
    updated_content: str = "Updated comment content",
) -> None:
    """Тест обновления комментария не создателем возвращает 403."""
    other_user: User = UserFactory()
    comment: Comment = CommentFactory(created_by=other_user, updated_by=other_user)
    url: str = reverse("api:comment-detail", kwargs={"pk": comment.pk})
    payload: dict[str, Any] = {
        "task": task.id,
        "content": updated_content,
    }

    response = authenticated_client.put(url, payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN


# Comment Delete Tests


def test_delete_comment_creator_returns_no_content(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест удаления комментария создателем возвращает 204."""
    comment: Comment = CommentFactory(created_by=user, updated_by=user)
    url: str = reverse("api:comment-detail", kwargs={"pk": comment.pk})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    comment.refresh_from_db()
    assert comment.is_deleted is True


def test_delete_comment_non_creator_returns_forbidden(
    authenticated_client: APIClient,
) -> None:
    """Тест удаления комментария не создателем возвращает 403."""
    other_user: User = UserFactory()
    comment: Comment = CommentFactory(created_by=other_user, updated_by=other_user)
    url: str = reverse("api:comment-detail", kwargs={"pk": comment.pk})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


# Comment Filtering Tests


def test_filter_comments_by_task_returns_filtered_results(
    authenticated_client: APIClient,
    comments_list_url: str = "/api/comments/",
) -> None:
    """Тест фильтрации комментариев по задаче возвращает отфильтрованные результаты."""
    task: Task = TaskFactory()
    matching_comment: Comment = CommentFactory(task=task)
    non_matching_comment: Comment = CommentFactory()

    response = authenticated_client.get(comments_list_url, {"task": task.id})

    assert response.status_code == status.HTTP_200_OK
    comment_ids: list[int] = [comment["id"] for comment in response.data["results"]]
    assert matching_comment.id in comment_ids
    assert non_matching_comment.id not in comment_ids


# Comment Ordering Tests


@pytest.mark.parametrize(
    "ordering_field,expected_first_index",
    [
        ("created_at", 0),
        ("-created_at", 2),
    ],
)
def test_order_comments_by_field_returns_ordered_results(
    authenticated_client: APIClient,
    task: Task,
    ordering_field: str,
    expected_first_index: int,
    comments_list_url: str = "/api/comments/",
) -> None:
    """Тест сортировки комментариев по полю возвращает отсортированные результаты."""
    comment1: Comment = CommentFactory(task=task)
    comment2: Comment = CommentFactory(task=task)
    comment3: Comment = CommentFactory(task=task)
    comments_list: list[Comment] = [comment1, comment2, comment3]

    response = authenticated_client.get(comments_list_url, {"ordering": ordering_field})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["id"] == comments_list[expected_first_index].id


# Inactive User Tests


def test_create_comment_inactive_user_returns_forbidden(
    api_client: APIClient,
    task: Task,
    comment_content: str = "Test comment",
) -> None:
    """Тест создания комментария неактивным пользователем возвращает 403."""
    inactive_user: User = UserFactory(is_active=False)
    api_client.force_authenticate(user=inactive_user)
    url: str = "/api/comments/"

    response = api_client.post(url, {"task": task.id, "content": comment_content})

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_comments_inactive_user_returns_forbidden(api_client: APIClient) -> None:
    """Тест получения списка комментариев неактивным пользователем возвращает 403."""
    inactive_user: User = UserFactory(is_active=False)
    api_client.force_authenticate(user=inactive_user)
    url: str = "/api/comments/"

    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


# Edge Case Tests


def test_create_comment_nonexistent_task_returns_bad_request(
    authenticated_client: APIClient,
    nonexistent_task_id: int = 99999,
    comment_content: str = "Test comment",
) -> None:
    """Тест создания комментария к несуществующей задаче возвращает 400."""
    url: str = "/api/comments/"

    response = authenticated_client.post(url, {"task": nonexistent_task_id, "content": comment_content})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "task" in response.data


def test_create_comment_deleted_task_returns_bad_request(
    authenticated_client: APIClient,
    user: User,
    comment_content: str = "Test comment",
) -> None:
    """Тест создания комментария к удаленной задаче возвращает 400."""
    deleted_task: Task = TaskFactory(created_by=user, updated_by=user, is_deleted=True)
    url: str = "/api/comments/"

    response = authenticated_client.post(url, {"task": deleted_task.id, "content": comment_content})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "task" in response.data


def test_update_comment_other_user_returns_forbidden(
    api_client: APIClient,
    updated_content: str = "Updated content",
) -> None:
    """Тест обновления комментария другим пользователем возвращает 403."""
    context = create_task_with_comments(comments_count=1)
    other_user: User = UserFactory()
    api_client.force_authenticate(user=other_user)
    comment = context.comments[0]
    url: str = reverse("api:comment-detail", kwargs={"pk": comment.pk})

    response = api_client.patch(url, {"content": updated_content})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    comment.refresh_from_db()
    assert comment.content != updated_content


def test_delete_comment_other_user_returns_forbidden(api_client: APIClient) -> None:
    """Тест удаления комментария другим пользователем возвращает 403."""
    context = create_task_with_comments(comments_count=1)
    other_user: User = UserFactory()
    api_client.force_authenticate(user=other_user)
    comment = context.comments[0]
    url: str = reverse("api:comment-detail", kwargs={"pk": comment.pk})

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    comment.refresh_from_db()
    assert comment.is_deleted is False
