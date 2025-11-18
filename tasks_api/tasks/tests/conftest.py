import pytest

from tasks_api.tasks.models import Tag, Task
from tasks_api.tasks.tests.factories import TagFactory, TaskFactory
from tasks_api.users.models import User


@pytest.fixture
def task(user: User) -> Task:
    return TaskFactory(created_by=user, updated_by=user)


@pytest.fixture
def tag(user: User) -> Tag:
    return TagFactory(created_by=user, updated_by=user)
