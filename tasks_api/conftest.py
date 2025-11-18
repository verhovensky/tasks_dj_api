import pytest
from rest_framework.test import APIClient

from tasks_api.users.models import User
from tasks_api.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def api_client() -> APIClient:
    """Фикстура для создания неаутентифицированного API клиента."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, user: User) -> APIClient:
    """Фикстура для создания аутентифицированного API клиента."""
    api_client.force_authenticate(user=user)
    return api_client
