import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tasks_api.users.models import User
from tasks_api.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_list_users_unauthenticated_returns_unauthorized(
    api_client: APIClient,
    users_list_url: str = "/api/users/",
) -> None:
    """Тест получения списка пользователей неаутентифицированным пользователем возвращает 401."""
    response = api_client.get(users_list_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_users_regular_user_returns_only_self(
    authenticated_client: APIClient,
    user: User,
    users_list_url: str = "/api/users/",
    other_users_count: int = 5,
    expected_count: int = 1,
) -> None:
    """Тест получения списка пользователей обычным пользователем возвращает только себя."""
    UserFactory.create_batch(other_users_count)

    response = authenticated_client.get(users_list_url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == expected_count
    assert response.data["results"][0]["name"] == user.name


def test_list_users_superuser_returns_all_users(
    api_client: APIClient,
    users_list_url: str = "/api/users/",
    total_users_count: int = 10,
) -> None:
    """Тест получения списка пользователей суперпользователем возвращает всех пользователей."""
    superuser: User = UserFactory(is_superuser=True)
    UserFactory.create_batch(total_users_count - 1)
    api_client.force_authenticate(user=superuser)

    response = api_client.get(users_list_url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == total_users_count


def test_retrieve_user_unauthenticated_returns_unauthorized(
    api_client: APIClient,
) -> None:
    """Тест получения пользователя неаутентифицированным пользователем возвращает 401."""
    user: User = UserFactory()
    url: str = reverse("api:user-detail", kwargs={"pk": user.pk})

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_user_self_returns_ok(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест получения собственного профиля возвращает 200."""
    url: str = reverse("api:user-detail", kwargs={"pk": user.pk})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == user.name
    assert "url" in response.data


def test_retrieve_other_user_regular_user_returns_not_found(
    authenticated_client: APIClient,
) -> None:
    """Тест получения другого пользователя обычным пользователем возвращает 404."""
    other_user: User = UserFactory()
    url: str = reverse("api:user-detail", kwargs={"pk": other_user.pk})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_retrieve_other_user_superuser_returns_ok(
    api_client: APIClient,
) -> None:
    """Тест получения другого пользователя суперпользователем возвращает 200."""
    superuser: User = UserFactory(is_superuser=True)
    other_user: User = UserFactory()
    api_client.force_authenticate(user=superuser)
    url: str = reverse("api:user-detail", kwargs={"pk": other_user.pk})

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == other_user.name


def test_retrieve_user_nonexistent_id_returns_not_found(
    authenticated_client: APIClient,
    nonexistent_id: int = 99999,
) -> None:
    """Тест получения несуществующего пользователя возвращает 404."""
    url: str = reverse("api:user-detail", kwargs={"pk": nonexistent_id})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_user_self_valid_data_returns_ok(
    authenticated_client: APIClient,
    user: User,
    updated_name: str = "Updated Name",
) -> None:
    """Тест обновления собственного профиля с валидными данными возвращает 200."""
    url: str = reverse("api:user-detail", kwargs={"pk": user.pk})
    payload: dict[str, str] = {"name": updated_name}

    response = authenticated_client.patch(url, payload)

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.name == updated_name


def test_update_user_other_user_returns_not_found(
    authenticated_client: APIClient,
    updated_name: str = "Updated Name",
) -> None:
    """Тест обновления другого пользователя обычным пользователем возвращает 404."""
    other_user: User = UserFactory()
    url: str = reverse("api:user-detail", kwargs={"pk": other_user.pk})
    payload: dict[str, str] = {"name": updated_name}

    response = authenticated_client.patch(url, payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    other_user.refresh_from_db()
    assert other_user.name != updated_name


def test_update_user_unauthenticated_returns_unauthorized(
    api_client: APIClient,
    updated_name: str = "Updated Name",
) -> None:
    """Тест обновления пользователя неаутентифицированным пользователем возвращает 401."""
    user: User = UserFactory()
    url: str = reverse("api:user-detail", kwargs={"pk": user.pk})
    payload: dict[str, str] = {"name": updated_name}

    response = api_client.patch(url, payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_user_me_endpoint_returns_current_user(
    authenticated_client: APIClient,
    user: User,
    users_me_url: str = "/api/users/me/",
) -> None:
    """Тест эндпоинта /me возвращает данные текущего пользователя."""
    response = authenticated_client.get(users_me_url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == user.name
    assert response.data["url"] == f"http://testserver/api/users/{user.pk}/"


def test_retrieve_user_me_unauthenticated_returns_unauthorized(
    api_client: APIClient,
    users_me_url: str = "/api/users/me/",
) -> None:
    """Тест эндпоинта /me неаутентифицированным пользователем возвращает 401."""
    response = api_client.get(users_me_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
