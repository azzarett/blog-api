from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils.translation import gettext_lazy as _

from apps.users.serializers import (
    RegisterResponseSerializer,
    RegisterSerializer,
    UpdateLanguageSerializer,
    UpdateTimezoneSerializer,
)
from apps.users.services import send_welcome_email

REGISTER_SUCCESS_STATUS = status.HTTP_201_CREATED
UPDATE_SUCCESS_STATUS = status.HTTP_200_OK


class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_welcome_email(user)

        payload = RegisterResponseSerializer.build_payload(user)
        response_serializer = RegisterResponseSerializer(instance=payload)
        return Response(response_serializer.data, status=REGISTER_SUCCESS_STATUS)


class UpdateLanguageAPIView(APIView):
    permission_classes = (IsAuthenticated,)

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
