from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.utils.translation import gettext_lazy as _

from apps.users.serializers import (
    ErrorDetailSerializer,
    MessageSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    TokenObtainRequestSerializer,
    TokenRefreshRequestSerializer,
    TokenRefreshResponseSerializer,
    TokenResponseSerializer,
    UpdateLanguageResponseSerializer,
    UpdateLanguageSerializer,
    UpdateTimezoneResponseSerializer,
    UpdateTimezoneSerializer,
    ValidationErrorResponseSerializer,
)
from apps.users.tasks import send_welcome_email

REGISTER_SUCCESS_STATUS = status.HTTP_201_CREATED
UPDATE_SUCCESS_STATUS = status.HTTP_200_OK


@extend_schema_view(
    create=extend_schema(
        tags=['Auth'],
        summary='Register a new user',
        description=(
            'Creates a new user account and returns JWT tokens. Authentication is '
            'not required. Side effect: sends a welcome email rendered from template '
            'in the language selected at registration and independent from request '
            'language at send time.'
        ),
        request=RegisterSerializer,
        responses={
            201: RegisterResponseSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Register request',
                request_only=True,
                value={
                    'email': 'user@example.com',
                    'first_name': 'Azat',
                    'last_name': 'Bertaeyev',
                    'preferred_language': 'ru',
                    'password': 'StrongPassword123!',
                    'password_confirm': 'StrongPassword123!',
                },
            ),
            OpenApiExample(
                'Register response',
                response_only=True,
                value={
                    'user': {
                        'email': 'user@example.com',
                        'first_name': 'Azat',
                        'last_name': 'Bertaeyev',
                        'preferred_language': 'ru',
                        'timezone': 'UTC',
                    },
                    'tokens': {
                        'refresh': '<jwt-refresh-token>',
                        'access': '<jwt-access-token>',
                    },
                },
            ),
        ],
    )
)
class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_welcome_email.delay(user.id)

        payload = RegisterResponseSerializer.build_payload(user)
        response_serializer = RegisterResponseSerializer(instance=payload)
        return Response(response_serializer.data, status=REGISTER_SUCCESS_STATUS)


class UpdateLanguageAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['Auth'],
        summary='Update preferred language',
        description=(
            'Updates language preference of the authenticated user. Requires JWT '
            'authentication. Side effect: subsequent requests resolve language from '
            'this profile value with highest priority.'
        ),
        request=UpdateLanguageSerializer,
        responses={
            200: UpdateLanguageResponseSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Language update request',
                request_only=True,
                value={'preferred_language': 'kk'},
            ),
            OpenApiExample(
                'Language update response',
                response_only=True,
                value={
                    'message': 'Preferred language updated successfully.',
                    'preferred_language': 'kk',
                },
            ),
        ],
    )
    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = UpdateLanguageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.preferred_language = serializer.validated_data[
            'preferred_language'
        ]
        request.user.save(update_fields=['preferred_language'])

        return Response(
            {
                'message': _('Preferred language updated successfully.'),
                'preferred_language': request.user.preferred_language,
            },
            status=UPDATE_SUCCESS_STATUS,
        )


class UpdateTimezoneAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['Auth'],
        summary='Update timezone',
        description=(
            'Updates timezone of the authenticated user. Requires JWT authentication. '
            'Timezone is validated against IANA identifiers. Side effect: post '
            'timestamps in API responses are converted to this timezone.'
        ),
        request=UpdateTimezoneSerializer,
        responses={
            200: UpdateTimezoneResponseSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Timezone update request',
                request_only=True,
                value={'timezone': 'Asia/Almaty'},
            ),
            OpenApiExample(
                'Timezone update response',
                response_only=True,
                value={
                    'message': 'Timezone updated successfully.',
                    'timezone': 'Asia/Almaty',
                },
            ),
        ],
    )
    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = UpdateTimezoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.timezone = serializer.validated_data['timezone']
        request.user.save(update_fields=['timezone'])

        return Response(
            {
                'message': _('Timezone updated successfully.'),
                'timezone': request.user.timezone,
            },
            status=UPDATE_SUCCESS_STATUS,
        )


@extend_schema_view(
    post=extend_schema(
        tags=['Auth'],
        summary='Obtain JWT token pair',
        description=(
            'Authenticates user credentials and returns access and refresh tokens. '
            'Authentication is not required.'
        ),
        request=TokenObtainRequestSerializer,
        responses={
            200: TokenResponseSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Token obtain request',
                request_only=True,
                value={'email': 'user@example.com', 'password': 'StrongPassword123!'},
            ),
            OpenApiExample(
                'Token obtain response',
                response_only=True,
                value={
                    'refresh': '<jwt-refresh-token>',
                    'access': '<jwt-access-token>',
                },
            ),
        ],
    )
)
class DocumentedTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)


@extend_schema_view(
    post=extend_schema(
        tags=['Auth'],
        summary='Refresh access token',
        description=(
            'Returns a new access token for a valid refresh token. '
            'Authentication is not required.'
        ),
        request=TokenRefreshRequestSerializer,
        responses={
            200: TokenRefreshResponseSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Token refresh request',
                request_only=True,
                value={'refresh': '<jwt-refresh-token>'},
            ),
            OpenApiExample(
                'Token refresh response',
                response_only=True,
                value={'access': '<jwt-access-token>'},
            ),
        ],
    )
)
class DocumentedTokenRefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)
