from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

EMAIL_FIELD = 'email'
FIRST_NAME_FIELD = 'first_name'
LAST_NAME_FIELD = 'last_name'
PASSWORD_FIELD = 'password'
PASSWORD_CONFIRM_FIELD = 'password_confirm'
REFRESH_FIELD = 'refresh'
ACCESS_FIELD = 'access'
TOKENS_FIELD = 'tokens'
PREFERRED_LANGUAGE_FIELD = 'preferred_language'
TIMEZONE_FIELD = 'timezone'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            EMAIL_FIELD,
            FIRST_NAME_FIELD,
            LAST_NAME_FIELD,
            PREFERRED_LANGUAGE_FIELD,
            TIMEZONE_FIELD,
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            EMAIL_FIELD,
            FIRST_NAME_FIELD,
            LAST_NAME_FIELD,
            PREFERRED_LANGUAGE_FIELD,
            PASSWORD_FIELD,
            PASSWORD_CONFIRM_FIELD,
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs[PASSWORD_FIELD] != attrs[PASSWORD_CONFIRM_FIELD]:
            raise serializers.ValidationError(
                {PASSWORD_CONFIRM_FIELD: _('Passwords do not match.')}
            )
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Any:
        validated_data.pop(PASSWORD_CONFIRM_FIELD)
        user_manager: Any = User.objects
        return user_manager.create_user(**validated_data)


class RegisterResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    tokens = serializers.DictField(child=serializers.CharField())

    @staticmethod
    def build_payload(user: Any) -> dict[str, Any]:
        refresh = RefreshToken.for_user(user)
        tokens = {
            REFRESH_FIELD: str(refresh),
            ACCESS_FIELD: str(refresh.access_token),
        }
        user_data = UserSerializer(user).data
        return {
            'user': user_data,
            TOKENS_FIELD: tokens,
        }


class UpdateLanguageSerializer(serializers.Serializer):
    preferred_language = serializers.ChoiceField(choices=User.Language.choices)


class UpdateTimezoneSerializer(serializers.Serializer):
    timezone = serializers.CharField()

    def validate_timezone(self, value: str) -> str:
        normalized_value = value.strip()

        try:
            ZoneInfo(normalized_value)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError(
                _(
                    "Invalid timezone. Use a valid IANA timezone identifier, "
                    "e.g. 'Asia/Almaty'."
                )
            ) from exc

        return normalized_value


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class UpdateLanguageResponseSerializer(MessageSerializer):
    preferred_language = serializers.ChoiceField(choices=User.Language.choices)


class UpdateTimezoneResponseSerializer(MessageSerializer):
    timezone = serializers.CharField()


class ErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ValidationErrorResponseSerializer(serializers.Serializer):
    non_field_errors = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    email = serializers.ListField(child=serializers.CharField(), required=False)
    first_name = serializers.ListField(child=serializers.CharField(), required=False)
    last_name = serializers.ListField(child=serializers.CharField(), required=False)
    password = serializers.ListField(child=serializers.CharField(), required=False)
    password_confirm = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    preferred_language = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    timezone = serializers.ListField(child=serializers.CharField(), required=False)


class TokenObtainRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
