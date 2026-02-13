from typing import Any

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

User = get_user_model()

EMAIL_FIELD = 'email'
FIRST_NAME_FIELD = 'first_name'
LAST_NAME_FIELD = 'last_name'
PASSWORD_FIELD = 'password'
PASSWORD_CONFIRM_FIELD = 'password_confirm'
REFRESH_FIELD = 'refresh'
ACCESS_FIELD = 'access'
TOKENS_FIELD = 'tokens'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (EMAIL_FIELD, FIRST_NAME_FIELD, LAST_NAME_FIELD)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            EMAIL_FIELD,
            FIRST_NAME_FIELD,
            LAST_NAME_FIELD,
            PASSWORD_FIELD,
            PASSWORD_CONFIRM_FIELD,
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs[PASSWORD_FIELD] != attrs[PASSWORD_CONFIRM_FIELD]:
            raise serializers.ValidationError(
                {PASSWORD_CONFIRM_FIELD: 'Passwords do not match.'}
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
