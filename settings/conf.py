from pathlib import Path

from decouple import Config, Csv, RepositoryEnv

SETTINGS_DIR = Path(__file__).resolve().parent
BASE_DIR = SETTINGS_DIR.parent

ENV_FILE_NAME = '.env'
ENV_FILE = SETTINGS_DIR / ENV_FILE_NAME
config = Config(RepositoryEnv(str(ENV_FILE)))

DEFAULT_ENV_ID = 'local'
DEFAULT_SECRET_KEY = 'unsafe-dev-secret-key'
DEFAULT_ALLOWED_HOSTS = ''
DEFAULT_TIME_ZONE = 'UTC'
DEFAULT_DB_NAME = 'blog_api'
DEFAULT_DB_USER = 'blog_user'
DEFAULT_DB_PASSWORD = 'blog_password'
DEFAULT_DB_HOST = '127.0.0.1'
DEFAULT_DB_PORT = '5432'

BLOG_ENV_ID = config('BLOG_ENV_ID', default=DEFAULT_ENV_ID)
BLOG_SECRET_KEY = config('BLOG_SECRET_KEY', default=DEFAULT_SECRET_KEY)
BLOG_ALLOWED_HOSTS = config(
    'BLOG_ALLOWED_HOSTS',
    default=DEFAULT_ALLOWED_HOSTS,
    cast=Csv(),
)
BLOG_TIME_ZONE = config('BLOG_TIME_ZONE', default=DEFAULT_TIME_ZONE)

BLOG_DB_NAME = config('BLOG_DB_NAME', default=DEFAULT_DB_NAME)
BLOG_DB_USER = config('BLOG_DB_USER', default=DEFAULT_DB_USER)
BLOG_DB_PASSWORD = config('BLOG_DB_PASSWORD', default=DEFAULT_DB_PASSWORD)
BLOG_DB_HOST = config('BLOG_DB_HOST', default=DEFAULT_DB_HOST)
BLOG_DB_PORT = config('BLOG_DB_PORT', default=DEFAULT_DB_PORT)
