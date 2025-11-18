from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from tasks_api.tasks.views import CommentViewSet, TagViewSet, TaskViewSet
from tasks_api.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("tasks", TaskViewSet, basename="task")
router.register("comments", CommentViewSet, basename="comment")
router.register("tags", TagViewSet, basename="tag")


app_name = "api"
urlpatterns = router.urls
