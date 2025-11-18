import pytest
from celery.result import EagerResult
from django.conf import settings as django_settings

from tasks_api.users.tasks import get_users_count
from tasks_api.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_get_users_count_task_returns_correct_count(
    settings: django_settings, expected_count: int = 3
) -> None:
    """Тест проверяет что задача Celery get_users_count возвращает корректное количество пользователей."""
    UserFactory.create_batch(expected_count)
    settings.CELERY_TASK_ALWAYS_EAGER = True
    task_result: EagerResult = get_users_count.delay()

    assert isinstance(task_result, EagerResult)
    assert task_result.result == expected_count
