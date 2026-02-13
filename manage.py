#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

from decouple import Config, RepositoryEnv


def get_settings_module() -> str:
    env_file = Path(__file__).resolve().parent / 'settings' / '.env'
    env_id = 'local'

    if env_file.exists():
        env_config = Config(RepositoryEnv(str(env_file)))
        env_id = env_config('BLOG_ENV_ID', default='local')

    return f'settings.env.{env_id}'


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_module())
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
