from typing import Any
from zoneinfo import ZoneInfo

from rest_framework_simplejwt.authentication import JWTAuthentication

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.utils import timezone, translation

from apps.users.models import User

DEFAULT_LANGUAGE = 'en'
DEFAULT_TIMEZONE = 'UTC'
SUPPORTED_LANGUAGES = {'en', 'ru', 'kk'}


class UserLocaleTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authentication = JWTAuthentication()

    def __call__(self, request: WSGIRequest) -> HttpResponse:
        user = self._get_authenticated_user(request)

        language = self._resolve_language(request, user)
        translation.activate(language)
        setattr(request, 'LANGUAGE_CODE', language)

        active_timezone = self._resolve_timezone(user)
        timezone.activate(active_timezone)

        response = self.get_response(request)
        response.headers.setdefault('Content-Language', language)

        translation.deactivate()
        timezone.deactivate()

        return response

    def _get_authenticated_user(self, request: WSGIRequest) -> User | None:
        request_user: Any = getattr(request, 'user', None)
        if getattr(request_user, 'is_authenticated', False):
            return request_user

        auth_header = request.headers.get('Authorization', '')
        if not auth_header:
            return None

        token_parts = auth_header.split()
        if len(token_parts) != 2:
            return None

        token_type, raw_token = token_parts
        if token_type not in {'Bearer', 'JWT'}:
            return None

        try:
            validated_token: Any = self.jwt_authentication.get_validated_token(
                raw_token.encode('utf-8')
            )
        except Exception:
            return None

        user_id = validated_token.get('user_id')
        if not user_id:
            return None

        return (
            User.objects.filter(id=user_id)
            .only('preferred_language', 'timezone')
            .first()
        )

    def _resolve_language(self, request: WSGIRequest, user: User | None) -> str:
        if user and user.preferred_language:
            normalized_user_language = self._normalize_language(user.preferred_language)
            if normalized_user_language:
                return normalized_user_language

        query_language = request.GET.get('lang')
        normalized_query_language = self._normalize_language(query_language)
        if normalized_query_language:
            return normalized_query_language

        accepted_header = request.headers.get('Accept-Language', '')
        for language_part in accepted_header.split(','):
            language_value = language_part.split(';', 1)[0].strip()
            normalized_header_language = self._normalize_language(language_value)
            if normalized_header_language:
                return normalized_header_language

        return DEFAULT_LANGUAGE

    def _normalize_language(self, value: str | None) -> str | None:
        if not value:
            return None

        normalized = value.lower().replace('_', '-').strip()
        if normalized in SUPPORTED_LANGUAGES:
            return normalized

        base_language = normalized.split('-', 1)[0]
        if base_language in SUPPORTED_LANGUAGES:
            return base_language

        return None

    def _resolve_timezone(self, user: User | None) -> ZoneInfo:
        if not user:
            return ZoneInfo(DEFAULT_TIMEZONE)

        if user.timezone:
            try:
                return ZoneInfo(user.timezone)
            except Exception:
                return ZoneInfo(DEFAULT_TIMEZONE)

        return ZoneInfo(DEFAULT_TIMEZONE)
