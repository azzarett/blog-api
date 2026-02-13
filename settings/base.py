from datetime import timedelta

from settings.conf import BLOG_ALLOWED_HOSTS, BLOG_SECRET_KEY, BLOG_TIME_ZONE

DJANGO_ADMIN_APP = 'django.contrib.admin'
DJANGO_AUTH_APP = 'django.contrib.auth'
DJANGO_CONTENTTYPES_APP = 'django.contrib.contenttypes'
DJANGO_SESSIONS_APP = 'django.contrib.sessions'
DJANGO_MESSAGES_APP = 'django.contrib.messages'
DJANGO_STATICFILES_APP = 'django.contrib.staticfiles'

DRF_APP = 'rest_framework'
USERS_APP = 'apps.users'
BLOG_APP = 'apps.blog'

ROOT_URLCONF_MODULE = 'settings.urls'
WSGI_APPLICATION_MODULE = 'settings.wsgi.application'
ASGI_APPLICATION_MODULE = 'settings.asgi.application'

DEFAULT_LANGUAGE_CODE = 'en-us'
STATIC_URL_PATH = 'static/'
DEFAULT_AUTO_FIELD_CLASS = 'django.db.models.BigAutoField'
AUTH_USER_MODEL_PATH = 'users.User'
JWT_AUTH_CLASS = 'rest_framework_simplejwt.authentication.JWTAuthentication'

USER_ATTRIBUTE_SIMILARITY_VALIDATOR = (
    'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
)
MINIMUM_LENGTH_VALIDATOR = (
    'django.contrib.auth.password_validation.MinimumLengthValidator'
)
COMMON_PASSWORD_VALIDATOR = (
    'django.contrib.auth.password_validation.CommonPasswordValidator'
)
NUMERIC_PASSWORD_VALIDATOR = (
    'django.contrib.auth.password_validation.NumericPasswordValidator'
)

ACCESS_TOKEN_LIFETIME_MINUTES = 15
REFRESH_TOKEN_LIFETIME_DAYS = 7

SECRET_KEY = BLOG_SECRET_KEY
DEBUG = False
ALLOWED_HOSTS = BLOG_ALLOWED_HOSTS

INSTALLED_APPS = [
    DJANGO_ADMIN_APP,
    DJANGO_AUTH_APP,
    DJANGO_CONTENTTYPES_APP,
    DJANGO_SESSIONS_APP,
    DJANGO_MESSAGES_APP,
    DJANGO_STATICFILES_APP,
    DRF_APP,
    USERS_APP,
    BLOG_APP,
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = ROOT_URLCONF_MODULE

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = WSGI_APPLICATION_MODULE
ASGI_APPLICATION = ASGI_APPLICATION_MODULE

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': USER_ATTRIBUTE_SIMILARITY_VALIDATOR,
    },
    {
        'NAME': MINIMUM_LENGTH_VALIDATOR,
    },
    {
        'NAME': COMMON_PASSWORD_VALIDATOR,
    },
    {
        'NAME': NUMERIC_PASSWORD_VALIDATOR,
    },
]

LANGUAGE_CODE = DEFAULT_LANGUAGE_CODE
TIME_ZONE = BLOG_TIME_ZONE
USE_I18N = True
USE_TZ = True

STATIC_URL = STATIC_URL_PATH
DEFAULT_AUTO_FIELD = DEFAULT_AUTO_FIELD_CLASS

AUTH_USER_MODEL = AUTH_USER_MODEL_PATH

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        JWT_AUTH_CLASS,
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS),
}
