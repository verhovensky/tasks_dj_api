from django.contrib.auth import get_user_model
from django.utils import timezone
from factory import Faker, LazyAttribute, SubFactory, post_generation
from factory.django import DjangoModelFactory

from tasks_api.tasks.enums import TaskPriority, TaskStatus
from tasks_api.tasks.models import Comment, Tag, Task
from tasks_api.users.tests.factories import UserFactory

User = get_user_model()


class TagFactory(DjangoModelFactory):
    name = Faker("word")
    color = LazyAttribute(
        lambda _: Faker("hex_color").evaluate(None, None, extra={"locale": None}),
    )
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)

    class Meta:
        model = Tag
        django_get_or_create = ["name"]


class TaskFactory(DjangoModelFactory):
    title = Faker("sentence", nb_words=5)
    description = Faker("paragraph")
    status = TaskStatus.TODO
    priority = TaskPriority.MEDIUM
    due_date = LazyAttribute(
        lambda _: timezone.now() + timezone.timedelta(days=7),
    )
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)
    assigned_to = None

    class Meta:
        model = Task

    @post_generation
    def tags(self, create, extracted, **kwargs):
        """Обработка many-to-many связи для тегов."""
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class CommentFactory(DjangoModelFactory):
    task = SubFactory(TaskFactory)
    content = Faker("paragraph")
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)

    class Meta:
        model = Comment
