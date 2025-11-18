## Tasks API

### Environment

Все переменные указываются в tasks_api/.envs/(local/production)
Сервисные команды находятся в Makefile


### Запуск

```sh
docker compose -f docker-compose.local.yml up --remove-orphans
```

При запуске создается админ (superuser) c email admin@admin.com в .envs/.local

Flower URL:
```
http://0.0.0.0:5555/
```
Sphinx docs URL:
```
http://0.0.0.0:9000
```
API URL:
```
http://0.0.0.0:8000
```
Admin:
```
http://0.0.0.0:8000/admin
```

Авторизоваться под созданным автоматически пользователем
```json
{
    "email": "admin@admin.com",
    "password": "PASSWORD"
}
```
Подставить токен в HTTP заголовке "Authorization: JWT $TOKEN" и делать запросы
Refresh token находиться в cookie с флагом HttpOnly

### Тесты

```sh
docker compose -f docker-compose.local.yml run --rm django sh -c "coverage run -m pytest && coverage report -m --skip-covered --sort=cover"
```

### TODO

1. Отправка подтверждения по [email, sms](https://dj-rest-auth.readthedocs.io/en/latest/api_endpoints.html#registration) через Celery
2. Добавить task/cron job (python manage.py flushexpiredtokens)
3. Storages для media
4. Доработать флоу с Tags
5. Фикс deprecated UserWarning (dj-rest-auth)
6. Фикс DeprecationWarning: UserFactory._after_postgeneration
7. make lint, make docker-lint
