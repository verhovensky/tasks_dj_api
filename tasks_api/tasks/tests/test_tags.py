import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tasks_api.tasks.models import Tag
from tasks_api.tasks.tests.factories import TagFactory
from tasks_api.users.models import User

pytestmark = pytest.mark.django_db


# Tag list Tests


def test_list_tags_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    tags_list_url: str = "/api/tags/",
) -> None:
    """Тест получения списка тегов неаутентифицированным пользователем возвращает 401."""
    response = api_client.get(tags_list_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_tags_authenticated_user_returns_ok(
    authenticated_client: APIClient,
    tags_list_url: str = "/api/tags/",
    batch_size: int = 3,
) -> None:
    """Тест получения списка тегов аутентифицированным пользователем возвращает 200."""
    TagFactory.create_batch(batch_size)

    response = authenticated_client.get(tags_list_url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == batch_size


def test_list_tags_excludes_deleted_tags_returns_only_active(
    authenticated_client: APIClient,
    tags_list_url: str = "/api/tags/",
) -> None:
    """Тест получения списка тегов исключает удаленные теги."""
    active_tag: Tag = TagFactory()
    deleted_tag: Tag = TagFactory(is_deleted=True)

    response = authenticated_client.get(tags_list_url)

    tag_ids: list[int] = [tag["id"] for tag in response.data["results"]]
    assert active_tag.id in tag_ids
    assert deleted_tag.id not in tag_ids


# Tag Create Tests


def test_create_tag_admin_user_valid_data_returns_created(
    admin_client,
    tags_list_url: str = "/api/tags/",
    tag_name: str = "urgent",
    tag_color: str = "#FF0000",
) -> None:
    """Тест создания тега админом с валидными данными возвращает 201."""
    payload: dict[str, str] = {
        "name": tag_name,
        "color": tag_color,
    }

    response = admin_client.post(tags_list_url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == tag_name
    assert response.data["color"] == tag_color


def test_create_tag_non_admin_user_returns_forbidden(
    authenticated_client: APIClient,
    tags_list_url: str = "/api/tags/",
    tag_name: str = "urgent",
) -> None:
    """Тест создания тега обычным пользователем возвращает 403."""
    payload: dict[str, str] = {"name": tag_name}

    response = authenticated_client.post(tags_list_url, payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_tag_without_color_returns_created(
    admin_client,
    tags_list_url: str = "/api/tags/",
    tag_name: str = "important",
) -> None:
    """Тест создания тега без цвета возвращает 201."""
    payload: dict[str, str] = {
        "name": tag_name,
    }

    response = admin_client.post(tags_list_url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == tag_name
    assert response.data["color"] is None


def test_create_tag_missing_required_name_returns_bad_request(
    admin_client,
    tags_list_url: str = "/api/tags/",
    tag_color: str = "#FF0000",
) -> None:
    """Тест создания тега без обязательного поля name возвращает 400."""
    payload: dict[str, str] = {
        "color": tag_color,
    }

    response = admin_client.post(tags_list_url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.data


def test_create_tag_duplicate_name_case_insensitive_returns_bad_request(
    admin_client,
    admin_user,
    tags_list_url: str = "/api/tags/",
    tag_name: str = "urgent",
) -> None:
    """Тест создания тега с дубликатом имени без учета регистра возвращает 400."""
    TagFactory(name=tag_name, created_by=admin_user, updated_by=admin_user)
    payload: dict[str, str] = {
        "name": tag_name.upper(),
    }

    response = admin_client.post(tags_list_url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.data


def test_create_tag_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    tags_list_url: str = "/api/tags/",
    tag_name: str = "urgent",
) -> None:
    """Тест создания тега неаутентифицированным пользователем возвращает 401."""
    payload: dict[str, str] = {"name": tag_name}

    response = api_client.post(tags_list_url, payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Tag Retrieve Tests


def test_retrieve_tag_authenticated_user_returns_ok(
    authenticated_client: APIClient,
    tag: Tag,
) -> None:
    """Тест получения детальной информации о теге возвращает 200."""
    url: str = reverse("api:tag-detail", kwargs={"pk": tag.pk})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == tag.id
    assert response.data["name"] == tag.name


def test_retrieve_tag_nonexistent_id_returns_not_found(
    authenticated_client: APIClient,
    nonexistent_id: int = 99999,
) -> None:
    """Тест получения несуществующего тега возвращает 404."""
    url: str = reverse("api:tag-detail", kwargs={"pk": nonexistent_id})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_retrieve_tag_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    tag: Tag,
) -> None:
    """Тест получения тега неаутентифицированным пользователем возвращает 401."""
    url: str = reverse("api:tag-detail", kwargs={"pk": tag.pk})

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Tag Update Tests (Tags don't support PUT/PATCH)


def test_update_tag_returns_method_not_allowed(
    authenticated_client: APIClient,
    tag: Tag,
    updated_name: str = "updated",
) -> None:
    """Тест обновления тега возвращает 405 (метод не поддерживается)."""
    url: str = reverse("api:tag-detail", kwargs={"pk": tag.pk})
    payload: dict[str, str] = {"name": updated_name}

    response = authenticated_client.put(url, payload)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_partial_update_tag_returns_method_not_allowed(
    authenticated_client: APIClient,
    tag: Tag,
    updated_name: str = "updated",
) -> None:
    """Тест частичного обновления тега возвращает 405 (метод не поддерживается)."""
    url: str = reverse("api:tag-detail", kwargs={"pk": tag.pk})
    payload: dict[str, str] = {"name": updated_name}

    response = authenticated_client.patch(url, payload)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# Tag Delete Tests


def test_delete_tag_admin_user_returns_no_content(
    admin_client,
    admin_user,
) -> None:
    """Тест удаления тега админом возвращает 204."""
    tag: Tag = TagFactory(created_by=admin_user, updated_by=admin_user)
    url: str = reverse("api:tag-detail", kwargs={"pk": tag.pk})

    response = admin_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Тег удаляется жестко, поэтому не должен существовать
    assert not Tag.objects.filter(pk=tag.pk).exists()


def test_delete_tag_non_admin_user_returns_forbidden(
    authenticated_client: APIClient,
    user: User,
) -> None:
    """Тест удаления тега обычным пользователем возвращает 403."""
    tag: Tag = TagFactory(created_by=user, updated_by=user)
    url: str = reverse("api:tag-detail", kwargs={"pk": tag.pk})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    # Тег не должен быть удален
    assert Tag.objects.filter(pk=tag.pk).exists()


def test_delete_tag_unauthenticated_user_returns_unauthorized(
    api_client: APIClient,
    tag: Tag,
) -> None:
    """Тест удаления тега неаутентифицированным пользователем возвращает 401."""
    url: str = reverse("api:tag-detail", kwargs={"pk": tag.pk})

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Tag Search Tests


def test_search_tags_by_name_returns_matching_results(
    authenticated_client: APIClient,
    tags_list_url: str = "/api/tags/",
    search_term: str = "urgent",
) -> None:
    """Тест поиска тегов по названию возвращает совпадающие результаты."""
    matching_tag: Tag = TagFactory(name=search_term)
    non_matching_tag: Tag = TagFactory(name="important")

    response = authenticated_client.get(tags_list_url, {"search": search_term})

    assert response.status_code == status.HTTP_200_OK
    tag_ids: list[int] = [tag["id"] for tag in response.data["results"]]
    assert matching_tag.id in tag_ids
    assert non_matching_tag.id not in tag_ids


# Tag Ordering Tests


@pytest.mark.parametrize(
    "ordering_field,expected_first_index",
    [
        ("name", 0),
        ("-name", 2),
        ("created_at", 0),
        ("-created_at", 2),
    ],
)
def test_order_tags_by_field_returns_ordered_results(
    authenticated_client: APIClient,
    user: User,
    ordering_field: str,
    expected_first_index: int,
    tags_list_url: str = "/api/tags/",
) -> None:
    """Тест сортировки тегов по полю возвращает отсортированные результаты."""
    tag1: Tag = TagFactory(name="alpha", created_by=user, updated_by=user)
    tag2: Tag = TagFactory(name="bravo", created_by=user, updated_by=user)
    tag3: Tag = TagFactory(name="charlie", created_by=user, updated_by=user)
    tags_list: list[Tag] = [tag1, tag2, tag3]

    response = authenticated_client.get(tags_list_url, {"ordering": ordering_field})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["id"] == tags_list[expected_first_index].id


# Tag Autocomplete Tests


def test_autocomplete_tags_with_query_returns_exact_match(
    authenticated_client: APIClient,
    search_query: str = "urgent",
) -> None:
    """Тест автозаполнения тегов с запросом возвращает точное совпадение."""
    matching_tag: Tag = TagFactory(name=search_query)
    non_matching_tag: Tag = TagFactory(name="important")
    url: str = reverse("api:tag-autocomplete")

    response = authenticated_client.get(url, {"q": search_query})

    assert response.status_code == status.HTTP_200_OK
    tag_ids: list[int] = [tag["id"] for tag in response.data]
    assert matching_tag.id in tag_ids
    assert non_matching_tag.id not in tag_ids


def test_autocomplete_tags_without_query_returns_limited_results(
    authenticated_client: APIClient,
    batch_size: int = 15,
    max_autocomplete_results: int = 10,
) -> None:
    """Тест автозаполнения тегов без запроса возвращает ограниченное количество результатов."""
    TagFactory.create_batch(batch_size)
    url: str = reverse("api:tag-autocomplete")

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == max_autocomplete_results


def test_autocomplete_tags_case_insensitive_match_returns_result(
    authenticated_client: APIClient,
    tag_name: str = "urgent",
) -> None:
    """Тест автозаполнения тегов с поиском без учета регистра возвращает результат."""
    matching_tag: Tag = TagFactory(name=tag_name)
    url: str = reverse("api:tag-autocomplete")

    response = authenticated_client.get(url, {"q": tag_name.upper()})

    assert response.status_code == status.HTTP_200_OK
    tag_ids: list[int] = [tag["id"] for tag in response.data]
    assert matching_tag.id in tag_ids
