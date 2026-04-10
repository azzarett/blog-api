# HW3 пошагово: что и как реализовать в blog-api

Этот файл создан как инструкция для новичка: делай строго по шагам, не перепрыгивай.

Цель: реализовать real-time коммуникации (WebSocket + SSE + Polling), Celery (async + beat), и Docker Compose запуск всей системы.

## 0) Перед стартом

1. Создай ветку:

```bash
git checkout -b hw3-realtime-celery-docker
```

2. Убедись, что локально поднимается текущее приложение:

```bash
source .venv/bin/activate
python manage.py check
python manage.py migrate
python manage.py runserver
```

3. Останови сервер и продолжай.

## 1) Установка зависимостей и базовая конфигурация

### 1.1 Обнови зависимости

Файл: `requirements/base.txt`

Добавь:
- `channels`
- `channels-redis`
- `celery`
- `flower`
- `daphne`

Потом установи:

```bash
pip install -r requirements/base.txt
```

### 1.2 Добавь новые env переменные

Файл: `settings/.env.example`

Добавь:

```env
BLOG_REDIS_URL=redis://redis:6379/0
BLOG_CELERY_BROKER_URL=redis://redis:6379/1
BLOG_FLOWER_USER=admin
BLOG_FLOWER_PASSWORD=changeme
BLOG_SEED_DB=false
```

### 1.3 Прочитай env в конфиге

Файл: `settings/conf.py`

Добавь переменные:
- `BLOG_CELERY_BROKER_URL`
- `BLOG_FLOWER_USER`
- `BLOG_FLOWER_PASSWORD`
- `BLOG_SEED_DB`

Важно: Redis для cache/channels и Redis для Celery broker должны быть разными DB (как в задании).

### 1.4 Подключи Channels в Django settings

Файл: `settings/base.py`

Сделай:
1. Добавь `channels` и новое приложение `apps.notifications` в `INSTALLED_APPS`.
2. Убедись, что `ASGI_APPLICATION = 'settings.asgi.application'`.
3. Добавь `CHANNEL_LAYERS`, например:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [BLOG_REDIS_URL],
        },
    },
}
```

### 1.5 Обнови ASGI под ProtocolTypeRouter

Файл: `settings/asgi.py`

Нужно:
- HTTP трафик оставить через `get_asgi_application()`.
- WebSocket трафик отправлять в `URLRouter` из `apps.notifications.routing`.

Итого структура: `ProtocolTypeRouter({'http': ..., 'websocket': ...})`.

Проверка этапа:

```bash
python manage.py check
```

## 2) Новое приложение notifications

Создай приложение:

```bash
python manage.py startapp notifications apps/notifications
```

Минимально должны появиться/быть:
- `apps/notifications/apps.py`
- `apps/notifications/models.py`
- `apps/notifications/views.py`
- `apps/notifications/tasks.py`
- `apps/notifications/consumers.py`
- `apps/notifications/routing.py`
- `apps/notifications/serializers.py`
- `apps/notifications/migrations/`

## 3) WebSockets: live comments

## 3.1 Routing WebSocket

Файл: `apps/notifications/routing.py`

Добавь маршрут:
- `ws/posts/<slug>/comments/` -> `CommentConsumer.as_asgi()`

### 3.2 Реализуй async consumer

Файл: `apps/notifications/consumers.py`

Сделай `AsyncWebsocketConsumer`:
1. В `connect`:
- достать `slug` из URL;
- достать JWT access token из query params (`?token=...`);
- провалидировать токен через SimpleJWT;
- если токен невалиден/нет пользователя -> `close(code=4001)`;
- если пост не найден -> `close(code=4004)`;
- добавить соединение в group с именем вроде `post_comments_<slug>`;
- `accept()`.

2. В `disconnect`:
- удалить канал из group.

3. Обработчик группового события (например `comment_created`):
- отправить JSON в сокет.

Формат сообщения строго:
- `comment_id`
- `author`: `{id, email}`
- `body`
- `created_at`

### 3.3 Публикация в group при создании комментария

По заданию side effects перенесем в Celery (см. шаг 7.3), но логика публикации должна в итоге идти через Channels layer `group_send`.

Проверка этапа (позже, когда будет Celery):
- открыть 2 клиента на один пост;
- создать комментарий через REST;
- оба клиента должны получить событие сразу.

## 4) HTTP Polling: notifications

### 4.1 Модель Notification

Файл: `apps/notifications/models.py`

Сделай модель:
- `recipient` -> FK на User, CASCADE
- `comment` -> FK на Comment, CASCADE
- `is_read` -> Boolean, default=False
- `created_at` -> DateTime auto_now_add

Дополнительно рекомендую:
- индекс по `(recipient, is_read)` для быстрого count.

Создай миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4.2 Сериализаторы и API

Файл: `apps/notifications/serializers.py`

Сделай сериализатор для списка уведомлений (включи минимум id, comment_id, is_read, created_at).

Файл: `apps/notifications/views.py`

Добавь 3 endpoint:
1. `GET /api/notifications/count/` (auth required) -> `{"unread_count": int}`
2. `GET /api/notifications/` (auth required, пагинация)
3. `POST /api/notifications/read/` (auth required) -> пометить все свои уведомления как read

Важно: добавь комментарий в коде про trade-off polling:
- плюс: просто внедрить;
- минус: задержка и лишняя нагрузка;
- когда переходить на SSE/WebSocket.

Файл: `settings/urls.py`

Зарегистрируй пути notifications API.

Проверка этапа:

```bash
python manage.py runserver
```

Проверь через Postman/Swagger:
- count работает,
- list пагинируется,
- read помечает записи.

## 5) SSE: поток публикаций постов

### 5.1 Endpoint stream

Файл: `apps/blog/views.py` (или отдельный view в notifications, но URL должен быть `/api/posts/stream/`)

Сделай async view:
- `GET /api/posts/stream/`
- `Content-Type: text/event-stream`
- ответ через `StreamingHttpResponse`
- бесконечный async генератор, который слушает backend fan-out (Redis Pub/Sub или Channels layer)

SSE формат:

```text
data: {json}\n\n
```

Payload:
- `post_id`
- `title`
- `slug`
- `author`: `{id, email}`
- `published_at`

Важно: в коде добавь комментарий, почему SSE хорошо подходит тут:
- только server -> client события,
- проще и дешевле WebSocket,
- если нужен bidirectional канал, тогда WebSocket.

### 5.2 Где триггерить SSE событие

Триггерить при переходе поста в `published`:
- создан сразу published,
- или обновлен из draft/scheduled -> published.

Можно сделать через signal `post_save` или в методах create/update viewset.

Проверка этапа:

```bash
curl -N http://127.0.0.1:8000/api/posts/stream/
```

Потом опубликуй пост и проверь, что в консоли пришло `data: ...`.

## 6) Расширение Post: scheduled публикации

Файл: `apps/blog/models.py`

1. Добавь новый статус `scheduled` в `Post.Status`.
2. Добавь поле `publish_at = DateTimeField(null=True, blank=True)`.

Сделай миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

Проверь, что существующие create/update сериализаторы корректно принимают новый статус и поле `publish_at`.

## 7) Celery: настройка и задачи

### 7.1 Базовая конфигурация Celery

Создай файл: `settings/celery.py`

Сделай:
1. Инициализация Celery app (`Celery('settings')`).
2. `config_from_object('django.conf:settings', namespace='CELERY')`.
3. `autodiscover_tasks()`.
4. Broker/backend = `BLOG_CELERY_BROKER_URL`.
5. Beat schedule (добавим в 8 разделе).

Файл: `settings/__init__.py`

Импортируй Celery app:

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

Файл: `settings/base.py`

Добавь celery-настройки:
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- при желании `CELERY_TIMEZONE`.

### 7.2 Перенеси welcome email в Celery

Файл: `apps/users/tasks.py`

Создай task отправки welcome email.

В месте регистрации пользователя (обычно `apps/users/views.py` или service) вызови задачу через `.delay(...)`.

### 7.3 Перенеси cache invalidation постов в Celery

Файл: `apps/blog/tasks.py`

Task: инвалидация/бамп кэша списка постов.

В create/update/delete постов вызывай task через `.delay()`.

### 7.4 Task process_new_comment

Файл: `apps/notifications/tasks.py`

Task должен делать ВСЕ side effects комментария:
1. Создавать Notification для автора поста (если комментатор не владелец).
2. Публиковать сообщение в WebSocket group через Channels layer.

В endpoint создания комментария (`POST /api/posts/{slug}/comments/`) после сохранения комментария вызывай:
- `process_new_comment.delay(comment_id=...)`

Важно: SSE публикации постов оставляй без Celery (по условию).

### 7.5 Retry policy для всех Celery tasks

Каждый task должен содержать:
- `autoretry_for=(Exception,)`
- `retry_backoff=True`
- `max_retries=3`

И комментарий в коде, зачем retry важен:
- email: временные SMTP сбои;
- cache invalidation: кратковременные Redis ошибки;
- comment processing: нельзя терять событие и уведомление.

Проверка этапа:

```bash
celery -A settings worker -l info
celery -A settings beat -l info
```

И создать тестовые действия через API.

## 8) Celery Beat: периодические задачи

### 8.1 publish_scheduled_posts (каждую минуту)

Файл: `apps/blog/tasks.py`

Task логика:
1. Найти посты `status=scheduled` и `publish_at <= now()`.
2. Обновить статус на `published`.
3. Для каждого поста отправить SSE событие публикации.

### 8.2 clear_expired_notifications (ежедневно 03:00)

Файл: `apps/notifications/tasks.py`

Удалить уведомления старше 30 дней.

### 8.3 generate_daily_stats (ежедневно 00:00)

Файл: можно `apps/blog/tasks.py` или `apps/core/tasks.py`.

Через `logger.info` вывести количество новых:
- posts
- comments
- users

за последние 24 часа.

### 8.4 Добавь расписание beat

Файл: `settings/celery.py`

Определи `beat_schedule`/`CELERY_BEAT_SCHEDULE` с 3 задачами.

Проверка:
- подними `celery beat`;
- проверь логи выполнения.

## 9) Flower мониторинг

Нужен запуск как отдельный сервис с basic auth из env:
- `BLOG_FLOWER_USER`
- `BLOG_FLOWER_PASSWORD`

Локальная проверка команды:

```bash
celery -A settings flower --basic-auth=${BLOG_FLOWER_USER}:${BLOG_FLOWER_PASSWORD}
```

Потом открой `http://localhost:5555`.

## 10) Dockerfile + entrypoint + compose

### 10.1 Dockerfile

Файл: `Dockerfile`

Требования:
1. base image `python:3.12-slim`
2. установить system deps (минимум `gettext`, плюс то, что нужно твоим пакетам)
3. поставить python requirements
4. скопировать код
5. создать non-root user и запускать от него
6. НЕ выполнять миграции/collectstatic внутри build
7. `ENTRYPOINT` на `scripts/entrypoint.sh`

### 10.2 Entrypoint script

Файл: `scripts/entrypoint.sh`

Алгоритм:
1. ждать Redis (цикл ping)
2. `python manage.py migrate`
3. `python manage.py collectstatic --noinput`
4. `python manage.py compilemessages`
5. если `BLOG_SEED_DB=true`, выполнить `python manage.py seed`
6. `exec "$@"`

Не забудь права:

```bash
chmod +x scripts/entrypoint.sh
```

### 10.3 Seed команда

Создай management command:
- `apps/<подходящее_приложение>/management/commands/seed.py`

Перенеси туда логику из `scripts/start.sh` (функция seed_database).

Команда должна запускаться отдельно:

```bash
python manage.py seed
```

### 10.4 docker-compose.yml

Файл: `docker-compose.yml`

Сервисы:
1. `web`: команда `daphne -b 0.0.0.0 -p 8000 settings.asgi:application`, порт `8000:8000`
2. `redis`: `redis:7-alpine`, порт `6379:6379`
3. `celery_worker`: `celery -A settings worker -l info`
4. `celery_beat`: `celery -A settings beat -l info`
5. `flower`: `celery -A settings flower --basic-auth=$BLOG_FLOWER_USER:$BLOG_FLOWER_PASSWORD`, порт `5555:5555`

Обязательно:
- один и тот же `env_file: settings/.env` у web/worker/beat/flower;
- `depends_on: [redis]` у web/worker/beat/flower;
- named volume для SQLite файла, чтобы данные сохранялись.

### 10.5 .dockerignore

Файл: `.dockerignore`

Добавь минимум:
- `.git`
- `.venv`
- `__pycache__`
- `*.pyc`
- `.pytest_cache`
- `.ruff_cache`
- `logs`
- `db.sqlite3` (если хочешь использовать volume-файл внутри контейнера)

Проверка этапа:

```bash
docker compose up --build
```

Проверь:
- API на 8000,
- Flower на 5555,
- worker/beat живы,
- WebSocket и SSE работают.

## 11) Что делать со старой listen_comments командой

Файл: `apps/blog/management/commands/listen_comments.py`

Варианты:
1. Удалить (предпочтительно, т.к. superseded).
2. Оставить как debug-инструмент, но перевести на Channels layer вместо raw Redis Pub/Sub.

## 12) Мини-чеклист после реализации

### Real-time
- WebSocket принимает только JWT и закрывает 4001 без auth.
- Несуществующий post slug -> close 4004.
- Новые комментарии пушатся всем подключенным клиентам.
- SSE stream отдает `text/event-stream` и шлет события публикации постов.

### Notifications polling
- `GET /api/notifications/count/` работает и требует auth.
- `GET /api/notifications/` пагинируется.
- `POST /api/notifications/read/` помечает уведомления read.

### Celery
- Все 3 async tasks вынесены в `tasks.py` соответствующих приложений.
- У всех tasks одинаковая retry policy.
- Beat задачи запускаются по расписанию.

### Docker
- `docker compose up --build` поднимает все сервисы.
- Daphne используется в web.
- Flower защищен basic auth из env.

## 13) Рекомендуемый порядок коммитов

1. `feat: add channels and notifications app skeleton`
2. `feat: implement websocket comments consumer with jwt auth`
3. `feat: add notifications polling api and model`
4. `feat: add sse post publication stream`
5. `feat: setup celery and move async side effects to tasks`
6. `feat: add celery beat scheduled tasks`
7. `chore: add dockerfile entrypoint compose and seed command`
8. `docs: update env example and hw3 guide`

Так будет проще дебажить и сдавать поэтапно.