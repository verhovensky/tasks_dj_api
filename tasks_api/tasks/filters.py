from django_filters import rest_framework as filters

from .models import Task


class TaskFilter(filters.FilterSet):
    priority = filters.NumberFilter()

    class Meta:
        model = Task
        fields = ["status", "assigned_to", "tags"]
