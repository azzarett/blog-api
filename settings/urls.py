from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.contrib import admin
from django.urls import path

ADMIN_PATH = 'admin/'
TOKEN_OBTAIN_PATH = 'api/token/'
TOKEN_REFRESH_PATH = 'api/token/refresh/'
TOKEN_OBTAIN_NAME = 'token_obtain_pair'
TOKEN_REFRESH_NAME = 'token_refresh'

urlpatterns = [
    path(ADMIN_PATH, admin.site.urls),
    path(TOKEN_OBTAIN_PATH, TokenObtainPairView.as_view(), name=TOKEN_OBTAIN_NAME),
    path(TOKEN_REFRESH_PATH, TokenRefreshView.as_view(), name=TOKEN_REFRESH_NAME),
]
