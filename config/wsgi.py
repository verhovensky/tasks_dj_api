"""
Конфигурация WSGI для проекта Tasks API.

Модуль содержит WSGI приложение для сервера разработки Django и production деплойментов.
Должен предоставлять переменную уровня модуля ``application``. Команды Django ``runserver``
и ``runfcgi`` находят приложение через настройку ``WSGI_APPLICATION``.

Обычно здесь стандартное Django WSGI приложение, но можно заменить его на кастомное,
которое делегирует запросы Django. Например, можно добавить WSGI middleware или
комбинировать Django с приложением другого фреймворка.

"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Упрощает размещение приложений в директории tasks_api.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(BASE_DIR / "tasks_api"))
# Используем DJANGO_SETTINGS_MODULE из окружения. Не работает при запуске нескольких
# сайтов в одном процессе mod_wsgi. Решение: режим daemon с отдельным процессом для каждого
# сайта или os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# Объект приложения для любого WSGI сервера. Включая сервер разработки Django,
# если настройка WSGI_APPLICATION указывает сюда.
application = get_wsgi_application()
# Применить WSGI middleware здесь.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
