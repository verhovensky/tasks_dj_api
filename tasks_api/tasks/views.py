from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import TaskFilter
from .models import Comment, Tag, Task
from .permissions import IsActiveUser, IsCreatorOrReadOnly
from .serializers import (
    CommentSerializer,
    TagSerializer,
    TaskAssignSerializer,
    TaskDetailSerializer,
    TaskSerializer,
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Список всех задач",
        description="Получить постраничный список всех задач. Поддерживает фильтрацию по статусу, приоритету, назначенному пользователю и тегам. Также поддерживает поиск и сортировку.",
        tags=["Задачи"],
        parameters=[
            OpenApiParameter(
                name="status",
                description="Фильтр по статусу задачи",
                required=False,
                type=str,
                enum=["pending", "in_progress", "completed"],
            ),
            OpenApiParameter(
                name="priority",
                description="Фильтр по уровню приоритета",
                required=False,
                type=str,
                enum=["low", "medium", "high"],
            ),
            OpenApiParameter(
                name="assigned_to",
                description="Фильтр по ID назначенного пользователя",
                required=False,
                type=int,
            ),
            OpenApiParameter(name="tags", description="Фильтр по ID тега", required=False, type=int),
            OpenApiParameter(
                name="search",
                description="Поиск в названии и описании",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Сортировка результатов по полю (префикс - для обратного порядка)",
                required=False,
                type=str,
            ),
        ],
        examples=[
            OpenApiExample(
                "Список задач",
                value={
                    "results": [
                        {
                            "id": 1,
                            "title": "Исправить ошибку в авторизации",
                            "status": "in_progress",
                            "priority": "high",
                        }
                    ]
                },
                response_only=True,
            ),
        ],
    ),
    create=extend_schema(
        summary="Создать новую задачу",
        description="Создать новую задачу. Аутентифицированный пользователь будет установлен как создатель.",
        tags=["Задачи"],
        examples=[
            OpenApiExample(
                "Пример создания задачи",
                value={
                    "title": "Реализовать новую функцию",
                    "description": "Добавить аутентификацию пользователя",
                    "priority": "high",
                    "due_date": "2025-12-31",
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Получить детали задачи",
        description="Получить подробную информацию о конкретной задаче, включая все комментарии.",
        tags=["Задачи"],
    ),
    update=extend_schema(
        summary="Обновить задачу",
        description="Обновить все поля задачи. Только создатель задачи может её обновить.",
        tags=["Задачи"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить задачу",
        description="Обновить отдельные поля задачи. Только создатель задачи может её обновить.",
        tags=["Задачи"],
    ),
    destroy=extend_schema(
        summary="Удалить задачу",
        description="Мягкое удаление задачи. Только создатель задачи может её удалить.",
        tags=["Задачи"],
    ),
)
class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления задачами.

    Предоставляет CRUD операции и дополнительные действия:
    - assign: назначить задачу пользователю
    - complete: отметить задачу как выполненную
    - mark_in_progress: отметить задачу как выполняющуюся
    - my_tasks: получить задачи текущего пользователя
    - assigned_to_me: получить задачи, назначенные текущему пользователю
    """

    queryset = (
        Task.objects.select_related("created_by", "updated_by", "assigned_to")
        .prefetch_related("tags", "comments")
        .filter(is_deleted=False)
    )
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsActiveUser, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "due_date", "priority", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Использовать детальный сериализатор для retrieve действия."""
        if self.action == "retrieve":
            return TaskDetailSerializer
        elif self.action == "assign":
            return TaskAssignSerializer
        return TaskSerializer

    def perform_create(self, serializer):
        """Установить created_by при создании задачи."""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """Установить updated_by при обновлении задачи."""
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """Мягкое удаление задачи."""
        instance.soft_delete()

    @extend_schema(
        summary="Назначить задачу пользователю",
        description="Назначить задачу активному пользователю. Ожидает в теле запроса ID пользователя.",
        tags=["Задачи"],
        request=TaskAssignSerializer,
        responses={status.HTTP_200_OK: TaskSerializer},
        examples=[
            OpenApiExample(
                "Пример назначения задачи",
                value={"user_id": 5},
                request_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """
        Назначить задачу пользователю.

        Ожидает в теле запроса: {"user_id": <id пользователя>}
        """
        task = self.get_object()
        serializer = TaskAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["assigned_to"]
        task.assign_to(user)
        task.updated_by = request.user
        task.save(update_fields=["updated_by", "updated_at"])

        return Response(TaskSerializer(task, context={"request": request}).data)

    @extend_schema(
        summary="Отметить задачу как выполненную",
        description="Изменить статус задачи на 'completed'.",
        tags=["Задачи"],
        request=None,
        responses={status.HTTP_200_OK: TaskSerializer},
    )
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Отметить задачу как выполненную."""
        task = self.get_object()
        task.mark_completed()
        task.updated_by = request.user
        task.save(update_fields=["updated_by", "updated_at"])
        serializer = TaskSerializer(task, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Отметить задачу как выполняющуюся",
        description="Изменить статус задачи на 'in_progress'.",
        tags=["Задачи"],
        request=None,
        responses={status.HTTP_200_OK: TaskSerializer},
    )
    @action(detail=True, methods=["post"])
    def mark_in_progress(self, request, pk=None):
        """Отметить задачу как выполняющуюся."""
        task = self.get_object()
        task.mark_in_progress()
        task.updated_by = request.user
        task.save(update_fields=["updated_by", "updated_at"])
        serializer = TaskSerializer(task, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Мои задачи",
        description="Получить список задач, созданных текущим пользователем.",
        tags=["Задачи"],
        responses={status.HTTP_200_OK: TaskSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def my_tasks(self, request):
        """Получить задачи, созданные текущим пользователем."""
        tasks = self.get_queryset().filter(created_by=request.user)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Задачи, назначенные мне",
        description="Получить список задач, назначенных текущему пользователю.",
        tags=["Задачи"],
        responses={status.HTTP_200_OK: TaskSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def assigned_to_me(self, request):
        """Получить задачи, назначенные текущему пользователю."""
        tasks = self.get_queryset().filter(assigned_to=request.user)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Список комментариев",
        description="Получить список всех комментариев. Можно фильтровать по задаче.",
        tags=["Комментарии"],
        parameters=[
            OpenApiParameter(name="task", description="Фильтр по ID задачи", required=False, type=int),
            OpenApiParameter(
                name="ordering",
                description="Сортировка результатов по полю",
                required=False,
                type=str,
            ),
        ],
    ),
    create=extend_schema(
        summary="Создать комментарий",
        description="Создать новый комментарий к задаче.",
        tags=["Комментарии"],
        examples=[
            OpenApiExample(
                "Пример создания комментария",
                value={"task": 1, "content": "Отличная работа!"},
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Получить комментарий",
        description="Получить детали конкретного комментария.",
        tags=["Комментарии"],
    ),
    update=extend_schema(
        summary="Обновить комментарий",
        description="Обновить комментарий. Только создатель может обновить комментарий.",
        tags=["Комментарии"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить комментарий",
        description="Обновить отдельные поля комментария. Только создатель может обновить комментарий.",
        tags=["Комментарии"],
    ),
    destroy=extend_schema(
        summary="Удалить комментарий",
        description="Мягкое удаление комментария. Только создатель может удалить комментарий.",
        tags=["Комментарии"],
    ),
)
class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления комментариями к задачам.

    Автоматически фильтрует комментарии по задаче, если указан параметр task_id.
    """

    queryset = Comment.objects.select_related("created_by", "task").filter(is_deleted=False)
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsActiveUser, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["task"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["created_at"]

    def perform_create(self, serializer):
        """Установить created_by при создании комментария."""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """Установить updated_by при обновлении комментария."""
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """Мягкое удаление комментария."""
        instance.soft_delete()


@extend_schema_view(
    list=extend_schema(
        summary="Список тегов",
        description="Получить список всех тегов. Поддерживает поиск по названию.",
        tags=["Теги"],
        parameters=[
            OpenApiParameter(
                name="search",
                description="Поиск по названию тега",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Сортировка результатов по полю",
                required=False,
                type=str,
            ),
        ],
    ),
    create=extend_schema(
        summary="Создать тег",
        description="Создать новый тег. Название тега уникально без учета регистра.",
        tags=["Теги"],
        examples=[
            OpenApiExample(
                "Пример создания тега",
                value={"name": "urgent", "color": "#FF0000"},
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Получить тег",
        description="Получить детали конкретного тега.",
        tags=["Теги"],
    ),
    destroy=extend_schema(
        summary="Удалить тег",
        description="Мягкое удаление тега.",
        tags=["Теги"],
    ),
)
class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления тегами.

    Предоставляет список тегов для автозаполнения и CRUD операции.
    Теги уникальны без учета регистра (Pizza = PIZZA = pizza).
    """

    queryset = Tag.objects.filter(is_deleted=False)
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_permissions(self):
        """Только админы могут создавать и удалять теги."""
        if self.action in ["create", "destroy"]:
            return [IsAuthenticated(), IsActiveUser(), permissions.IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Установить created_by при создании тега."""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    @extend_schema(
        summary="Автозаполнение тегов",
        description="Получить теги для автозаполнения. Принимает параметр ?q=<поисковый запрос> и возвращает точное совпадение без учета регистра.",
        tags=["Теги"],
        parameters=[
            OpenApiParameter(
                name="q",
                description="Поисковый запрос для автозаполнения",
                required=False,
                type=str,
            ),
        ],
        responses={status.HTTP_200_OK: TagSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Автозаполнение тегов",
                value=[{"id": 1, "name": "urgent", "color": "#FF0000"}],
                response_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        """
        Endpoint для автозаполнения тегов.

        Принимает параметр ?q=<search term> и возвращает точное совпадение (без учета регистра).
        """
        query = request.query_params.get("q", "")
        if query:
            # Точное совпадение без учета регистра
            tags = self.get_queryset().filter(name__iexact=query)
        else:
            tags = self.get_queryset()[:10]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)
