#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

from decouple import Config, RepositoryEnv

SETTINGS_DIR_NAME = 'settings'
ENV_FILE_NAME = '.env'
DEFAULT_ENV_ID = 'local'
ENV_ID_KEY = 'BLOG_ENV_ID'
DJANGO_SETTINGS_MODULE_KEY = 'DJANGO_SETTINGS_MODULE'
SETTINGS_MODULE_TEMPLATE = 'settings.env.{env_id}'


def get_settings_module() -> str:
    env_file = Path(__file__).resolve().parent / SETTINGS_DIR_NAME / ENV_FILE_NAME
    env_id = DEFAULT_ENV_ID

    if env_file.exists():
        env_config = Config(RepositoryEnv(str(env_file)))
        env_id = env_config(ENV_ID_KEY, default=DEFAULT_ENV_ID)

    return SETTINGS_MODULE_TEMPLATE.format(env_id=env_id)


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault(DJANGO_SETTINGS_MODULE_KEY, get_settings_module())
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
