from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.users.managers import UserManager

MAX_NAME_LENGTH = 50
LANGUAGE_CODE_MAX_LENGTH = 10
TIMEZONE_MAX_LENGTH = 64
DEFAULT_PREFERRED_LANGUAGE = 'en'
DEFAULT_TIMEZONE = 'UTC'


class User(AbstractBaseUser, PermissionsMixin):
    class Language(models.TextChoices):
        ENGLISH = 'en', 'English'
        RUSSIAN = 'ru', 'Russian'
        KAZAKH = 'kk', 'Kazakh'

    email = models.EmailField(unique=True)
    first_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_('First name'),
    )
    last_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_('Last name'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'))
    is_staff = models.BooleanField(default=False, verbose_name=_('Is staff'))
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Date joined'),
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name=_('Avatar'),
    )
    preferred_language = models.CharField(
        max_length=LANGUAGE_CODE_MAX_LENGTH,
        choices=Language.choices,
        default=DEFAULT_PREFERRED_LANGUAGE,
        verbose_name=_('Preferred language'),
    )
    timezone = models.CharField(
        max_length=TIMEZONE_MAX_LENGTH,
        default=DEFAULT_TIMEZONE,
        verbose_name=_('Timezone'),
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self) -> str:
        return self.email
