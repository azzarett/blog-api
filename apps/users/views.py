from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.serializers import (
    RegisterResponseSerializer,
    RegisterSerializer,
)

REGISTER_SUCCESS_STATUS = status.HTTP_201_CREATED


class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        payload = RegisterResponseSerializer.build_payload(user)
        response_serializer = RegisterResponseSerializer(instance=payload)
        return Response(response_serializer.data, status=REGISTER_SUCCESS_STATUS)
