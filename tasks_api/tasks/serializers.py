from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Comment, Tag, Task

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name"]
        read_only_fields = ["id", "email", "name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "uuid", "name", "color", "created_at", "updated_at"]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]

    def validate_name(self, value):
        """Проверяет уникальность имени тега без учета регистра."""
        queryset = Tag.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Тег с таким именем уже существует (регистр не учитывается).")
        return value


class CommentSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(source="created_by", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "uuid",
            "task",
            "content",
            "author",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "author", "created_at", "updated_at"]

    def validate_task(self, value):
        """Проверяет что задача не удалена."""
        if value.is_deleted:
            raise serializers.ValidationError("Невозможно создать комментарий к удаленной задаче.")
        return value


class TaskSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Task с вложенными данными тегов и назначенного пользователя.
    Включает вычисляемые поля, такие как is_overdue.
    """

    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source="tags",
        write_only=True,
        required=False,
    )
    assigned_to = UserMinimalSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="assigned_to",
        write_only=True,
        required=False,
        allow_null=True,
    )
    created_by = UserMinimalSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "uuid",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "assigned_to",
            "assigned_to_id",
            "tags",
            "tag_ids",
            "created_by",
            "is_overdue",
            "is_completed",
            "comments_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "created_by",
            "is_overdue",
            "is_completed",
            "comments_count",
            "created_at",
            "updated_at",
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()

    def create(self, validated_data):
        """
        Создает задачу и корректно обрабатывает ManyToMany поле tags.
        """
        tags = validated_data.pop("tags", [])
        task = Task.objects.create(**validated_data)
        if tags:
            task.tags.set(tags)
        return task

    def update(self, instance, validated_data):
        """
        Обновляет задачу и корректно обрабатывает ManyToMany поле tags.
        """
        tags = validated_data.pop("tags", None)
        # Обновляем все обычные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance


class TaskDetailSerializer(TaskSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ["comments"]


class TaskAssignSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="assigned_to",
        help_text="ID активного пользователя, которому назначается задача",
    )
