import os

from celery import Celery

# Установка модуля настроек Django по умолчанию для Celery.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("tasks_api")

# Использование строки означает, что worker не сериализует объект настроек в дочерние процессы.
# namespace='CELERY' означает, что все ключи конфигурации Celery должны иметь префикс `CELERY_`.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Загрузка модулей задач из всех зарегистрированных приложений Django.
app.autodiscover_tasks()
