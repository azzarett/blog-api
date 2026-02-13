from typing import TYPE_CHECKING

from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from apps.users.models import User


class UserManager(BaseUserManager):
    def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> 'User':
        if not email:
            raise ValueError('The email field is required.')
        if not first_name:
            raise ValueError('The first_name field is required.')
        if not last_name:
            raise ValueError('The last_name field is required.')

        normalized_email = self.normalize_email(email).lower()
        user = self.model(
            email=normalized_email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        **extra_fields: object,
    ) -> 'User':
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields,
        )
