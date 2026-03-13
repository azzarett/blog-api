#!/usr/bin/env bash
set -Eeuo pipefail

CURRENT_STEP="initialization"
SERVER_PID=""

on_error() {
  local exit_code=$?
  printf '[start.sh] ERROR: Step failed: %s\n' "$CURRENT_STEP" >&2
  exit "$exit_code"
}

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
}

trap on_error ERR
trap cleanup EXIT INT TERM

log() {
  printf '[start.sh] %s\n' "$1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/settings/.env"
VENV_DIR="${PROJECT_ROOT}/.venv"

SUPERUSER_EMAIL="admin@blog.local"
SUPERUSER_PASSWORD="Admin123!"
SUPERUSER_FIRST_NAME="Admin"
SUPERUSER_LAST_NAME="User"

HOST="127.0.0.1"
PORT="8000"

run_step() {
  CURRENT_STEP="$1"
  log "$CURRENT_STEP"
  shift
  "$@"
}

check_required_env_vars() {
  if [[ ! -f "$ENV_FILE" ]]; then
    printf '[start.sh] Missing required env file: %s\n' "$ENV_FILE" >&2
    return 1
  fi

  python3 - "$ENV_FILE" "${PROJECT_ROOT}/settings/conf.py" <<'PY'
import re
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
conf_path = Path(sys.argv[2])

required_vars = sorted(set(re.findall(r"config\('([A-Z0-9_]+)'", conf_path.read_text())))

values: dict[str, str] = {}
for raw_line in env_path.read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue

    if line.startswith("export "):
        line = line[len("export ") :].strip()

    if "=" not in line:
        continue

    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()

    if "#" in value and not (value.startswith('"') or value.startswith("'")):
        value = value.split("#", 1)[0].strip()

    if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
        value = value[1:-1]

    values[key] = value

missing = [var for var in required_vars if values.get(var, "").strip() == ""]

if missing:
    for var in missing:
        print(f"Missing required env variable: {var}", file=sys.stderr)
    sys.exit(1)

print(f"Validated {len(required_vars)} required environment variables from {env_path}.")
PY
}

setup_venv_and_deps() {
  cd "$PROJECT_ROOT"

  if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
    log "Created virtual environment at ${VENV_DIR}."
  else
    log "Virtual environment already exists at ${VENV_DIR}; reusing."
  fi

  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"

  python -m pip install --upgrade pip

  if [[ -f "${PROJECT_ROOT}/requirements/dev.txt" ]]; then
    pip install -r "${PROJECT_ROOT}/requirements/dev.txt"
  else
    pip install -r "${PROJECT_ROOT}/requirements/base.txt"
  fi
}

run_migrations() {
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"
  python manage.py migrate --noinput
}

collect_static_files() {
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"

  python - <<'PY'
import os
from pathlib import Path

from manage import get_settings_module

os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_settings_module())

import django

django.setup()

from django.conf import settings
from django.core.management import call_command

settings.STATIC_ROOT = str(Path(settings.BASE_DIR) / "staticfiles")
call_command("collectstatic", interactive=False, verbosity=0)
print(f"Collected static files into {settings.STATIC_ROOT}.")
PY
}

compile_translations() {
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"
  python manage.py compilemessages --ignore=.venv --ignore=.git
}

create_or_update_superuser() {
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"

  python manage.py shell <<PY
from django.contrib.auth import get_user_model

User = get_user_model()
email = "${SUPERUSER_EMAIL}".strip().lower()
password = "${SUPERUSER_PASSWORD}"

user, created = User.objects.get_or_create(
    email=email,
    defaults={
        "first_name": "${SUPERUSER_FIRST_NAME}",
        "last_name": "${SUPERUSER_LAST_NAME}",
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
    },
)

changed = False
if user.first_name != "${SUPERUSER_FIRST_NAME}":
    user.first_name = "${SUPERUSER_FIRST_NAME}"
    changed = True
if user.last_name != "${SUPERUSER_LAST_NAME}":
    user.last_name = "${SUPERUSER_LAST_NAME}"
    changed = True
if not user.is_staff:
    user.is_staff = True
    changed = True
if not user.is_superuser:
    user.is_superuser = True
    changed = True
if not user.is_active:
    user.is_active = True
    changed = True

user.set_password(password)
changed = True

if changed:
    user.save()

if created:
    print(f"Created superuser: {email}")
else:
    print(f"Superuser already existed, credentials refreshed: {email}")
PY
}

seed_database() {
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"

  python manage.py shell <<'PY'
from django.contrib.auth import get_user_model

from apps.blog.models import Category, Comment, Post, Tag

User = get_user_model()

user_specs = [
    ("anna@example.com", "Anna", "Ivanova", "ru", "Europe/Moscow"),
    ("berik@example.com", "Berik", "Sadykov", "kk", "Asia/Almaty"),
    ("john@example.com", "John", "Carter", "en", "UTC"),
    ("maria@example.com", "Maria", "Petrova", "ru", "Europe/Samara"),
    ("aigerim@example.com", "Aigerim", "Nur", "kk", "Asia/Aqtobe"),
    ("tom@example.com", "Tom", "Lee", "en", "America/New_York"),
]

users = []
for index, (email, first_name, last_name, language, timezone_name) in enumerate(user_specs, start=1):
    user, _ = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "preferred_language": language,
            "timezone": timezone_name,
            "is_active": True,
        },
    )

    user.first_name = first_name
    user.last_name = last_name
    user.preferred_language = language
    user.timezone = timezone_name
    user.is_active = True
    user.set_password(f"UserPass{index}!")
    user.save()

    users.append(user)

category_specs = [
    ("Technology", "Технологии", "Технология", "technology"),
    ("Education", "Образование", "Білім", "education"),
    ("Travel", "Путешествия", "Саяхат", "travel"),
    ("Health", "Здоровье", "Денсаулық", "health"),
    ("Business", "Бизнес", "Бизнес", "business"),
]

categories = []
for name, name_ru, name_kk, slug in category_specs:
    category, _ = Category.objects.update_or_create(
        slug=slug,
        defaults={
            "name": name,
            "name_ru": name_ru,
            "name_kk": name_kk,
        },
    )
    categories.append(category)


tag_specs = [
    ("django", "django"),
    ("python", "python"),
    ("api", "api"),
    ("testing", "testing"),
    ("devops", "devops"),
    ("frontend", "frontend"),
    ("backend", "backend"),
    ("postgres", "postgres"),
    ("sqlite", "sqlite"),
    ("localization", "localization"),
]

all_tags = []
for name, slug in tag_specs:
    tag, _ = Tag.objects.update_or_create(slug=slug, defaults={"name": name})
    all_tags.append(tag)

created_posts = 0
updated_posts = 0
for i in range(1, 37):
    author = users[(i - 1) % len(users)]
    category = categories[(i - 1) % len(categories)]
    status = Post.Status.PUBLISHED if i % 3 != 0 else Post.Status.DRAFT
    slug = f"sample-post-{i:02d}"

    post, created = Post.objects.get_or_create(
        slug=slug,
        defaults={
            "author": author,
            "title": f"Sample Post {i:02d}",
            "body": (
                f"This is sample body text for post {i}. "
                "It is long enough for list/detail views and realistic pagination checks."
            ),
            "category": category,
            "status": status,
        },
    )

    post.author = author
    post.title = f"Sample Post {i:02d}"
    post.body = (
        f"This is sample body text for post {i}. "
        "Use it to test pagination, cache behavior, and localized category names."
    )
    post.category = category
    post.status = status
    post.save()

    if created:
        created_posts += 1
    else:
        updated_posts += 1

    tag_indexes = [i % len(all_tags), (i + 2) % len(all_tags), (i + 5) % len(all_tags)]
    post.tags.set([all_tags[idx] for idx in tag_indexes])

published_posts = list(Post.objects.filter(status=Post.Status.PUBLISHED).order_by("id")[:20])
comment_templates = [
    "Great explanation, thanks!",
    "I tested this approach locally and it worked.",
    "Could you share more details about edge cases?",
    "Localization example is very helpful.",
    "This post should be in the docs.",
]

created_comments = 0
for post_index, post in enumerate(published_posts, start=1):
    for comment_index in range(4):
        author = users[(post_index + comment_index) % len(users)]
        body = (
            f"[{post.slug}] {comment_templates[comment_index % len(comment_templates)]} "
            f"Comment #{comment_index + 1}."
        )
        _, created = Comment.objects.get_or_create(
            post=post,
            author=author,
            body=body,
        )
        if created:
            created_comments += 1

print(
    "Seed complete: "
    f"users={User.objects.count()}, "
    f"categories={Category.objects.count()}, "
    f"tags={Tag.objects.count()}, "
    f"posts={Post.objects.count()} (created={created_posts}, updated={updated_posts}), "
    f"comments={Comment.objects.count()} (created={created_comments})."
)
PY
}

wait_for_server() {
  python3 - "$HOST" "$PORT" <<'PY'
import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])

deadline = time.time() + 30
while time.time() < deadline:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        if sock.connect_ex((host, port)) == 0:
            sys.exit(0)
    time.sleep(0.5)

print(f"Server did not become ready in time at http://{host}:{port}", file=sys.stderr)
sys.exit(1)
PY
}

start_dev_server() {
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"

  python manage.py runserver "${HOST}:${PORT}" &
  SERVER_PID=$!

  wait_for_server

  printf '\n[start.sh] Project is running.\n'
  printf '[start.sh] API:      http://%s:%s/api/posts/\n' "$HOST" "$PORT"
  printf '[start.sh] Swagger:  http://%s:%s/api/docs/\n' "$HOST" "$PORT"
  printf '[start.sh] ReDoc:    http://%s:%s/api/redoc/\n' "$HOST" "$PORT"
  printf '[start.sh] Admin:    http://%s:%s/admin/\n' "$HOST" "$PORT"
  printf '[start.sh] Superuser credentials: %s / %s\n\n' "$SUPERUSER_EMAIL" "$SUPERUSER_PASSWORD"

  wait "$SERVER_PID"
}

run_step "Validate required .env variables" check_required_env_vars
run_step "Create virtual environment and install dependencies" setup_venv_and_deps
run_step "Run database migrations" run_migrations
run_step "Collect static files" collect_static_files
run_step "Compile translation files" compile_translations
run_step "Create or update superuser" create_or_update_superuser
run_step "Seed database with realistic test data" seed_database
run_step "Start development server" start_dev_server
