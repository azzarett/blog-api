from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.contrib import admin
from django.urls import path

from apps.users.views import RegisterViewSet

ADMIN_PATH = 'admin/'
REGISTER_PATH = 'api/auth/register/'
TOKEN_OBTAIN_PATH = 'api/auth/token/'
TOKEN_REFRESH_PATH = 'api/auth/token/refresh/'
REGISTER_NAME = 'auth_register'
TOKEN_OBTAIN_NAME = 'auth_token_obtain_pair'
TOKEN_REFRESH_NAME = 'auth_token_refresh'

REGISTER_ACTION_MAP = {'post': 'create'}

urlpatterns = [
    path(ADMIN_PATH, admin.site.urls),
    path(
        REGISTER_PATH,
        RegisterViewSet.as_view(REGISTER_ACTION_MAP),
        name=REGISTER_NAME,
    ),
    path(TOKEN_OBTAIN_PATH, TokenObtainPairView.as_view(), name=TOKEN_OBTAIN_NAME),
    path(TOKEN_REFRESH_PATH, TokenRefreshView.as_view(), name=TOKEN_REFRESH_NAME),
]
