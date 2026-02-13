from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User

EMAIL_FIELD = 'email'
FIRST_NAME_FIELD = 'first_name'
LAST_NAME_FIELD = 'last_name'
IS_STAFF_FIELD = 'is_staff'
IS_ACTIVE_FIELD = 'is_active'
PASSWORD_FIELD = 'password'
AVATAR_FIELD = 'avatar'
IS_SUPERUSER_FIELD = 'is_superuser'
GROUPS_FIELD = 'groups'
USER_PERMISSIONS_FIELD = 'user_permissions'
LAST_LOGIN_FIELD = 'last_login'
DATE_JOINED_FIELD = 'date_joined'
PASSWORD_1_FIELD = 'password1'
PASSWORD_2_FIELD = 'password2'

PERSONAL_INFO_SECTION = 'Personal info'
PERMISSIONS_SECTION = 'Permissions'
IMPORTANT_DATES_SECTION = 'Important dates'
WIDE_CLASS = 'wide'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = (EMAIL_FIELD,)
    list_display = (
        EMAIL_FIELD,
        FIRST_NAME_FIELD,
        LAST_NAME_FIELD,
        IS_STAFF_FIELD,
        IS_ACTIVE_FIELD,
    )
    search_fields = (EMAIL_FIELD, FIRST_NAME_FIELD, LAST_NAME_FIELD)

    fieldsets = (
        (None, {'fields': (EMAIL_FIELD, PASSWORD_FIELD)}),
        (
            PERSONAL_INFO_SECTION,
            {'fields': (FIRST_NAME_FIELD, LAST_NAME_FIELD, AVATAR_FIELD)},
        ),
        (
            PERMISSIONS_SECTION,
            {
                'fields': (
                    IS_ACTIVE_FIELD,
                    IS_STAFF_FIELD,
                    IS_SUPERUSER_FIELD,
                    GROUPS_FIELD,
                    USER_PERMISSIONS_FIELD,
                )
            },
        ),
        (IMPORTANT_DATES_SECTION, {'fields': (LAST_LOGIN_FIELD, DATE_JOINED_FIELD)}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': (WIDE_CLASS,),
                'fields': (
                    EMAIL_FIELD,
                    FIRST_NAME_FIELD,
                    LAST_NAME_FIELD,
                    PASSWORD_1_FIELD,
                    PASSWORD_2_FIELD,
                    IS_STAFF_FIELD,
                    IS_ACTIVE_FIELD,
                ),
            },
        ),
    )
