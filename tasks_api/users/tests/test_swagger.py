import pytest
from django.test import Client
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_swagger_ui_accessible_by_admin_returns_ok(admin_client: Client) -> None:
    """Тест проверяет что Swagger UI доступен администратору."""
    url: str = reverse("api-docs")
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_swagger_ui_unauthenticated_user_returns_unauthorized(client: Client) -> None:
    """Тест проверяет что Swagger UI недоступен обычному пользователю."""
    url: str = reverse("api-docs")
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_api_schema_generated_successfully_returns_ok(admin_client: Client) -> None:
    """Тест проверяет что API схема успешно генерируется для администратора."""
    url: str = reverse("api-schema")
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
