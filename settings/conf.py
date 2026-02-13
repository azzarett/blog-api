from pathlib import Path

from decouple import Config, Csv, RepositoryEnv

SETTINGS_DIR = Path(__file__).resolve().parent
BASE_DIR = SETTINGS_DIR.parent

ENV_FILE = SETTINGS_DIR / '.env'
config = Config(RepositoryEnv(str(ENV_FILE)))

BLOG_ENV_ID = config('BLOG_ENV_ID', default='local')
BLOG_SECRET_KEY = config('BLOG_SECRET_KEY', default='unsafe-dev-secret-key')
BLOG_ALLOWED_HOSTS = config('BLOG_ALLOWED_HOSTS', default='', cast=Csv())
BLOG_TIME_ZONE = config('BLOG_TIME_ZONE', default='UTC')

BLOG_DB_NAME = config('BLOG_DB_NAME', default='blog_api')
BLOG_DB_USER = config('BLOG_DB_USER', default='blog_user')
BLOG_DB_PASSWORD = config('BLOG_DB_PASSWORD', default='blog_password')
BLOG_DB_HOST = config('BLOG_DB_HOST', default='127.0.0.1')
BLOG_DB_PORT = config('BLOG_DB_PORT', default='5432')
