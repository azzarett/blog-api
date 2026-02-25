from rest_framework_nested.routers import NestedDefaultRouter

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.contrib import admin
from django.urls import include, path

from apps.blog.views import CommentViewSet, PostViewSet
from apps.users.views import (
    RegisterViewSet,
    UpdateLanguageAPIView,
    UpdateTimezoneAPIView,
)

ADMIN_PATH = 'admin/'
REGISTER_PATH = 'api/auth/register/'
TOKEN_OBTAIN_PATH = 'api/auth/token/'
TOKEN_REFRESH_PATH = 'api/auth/token/refresh/'
UPDATE_LANGUAGE_PATH = 'api/auth/language/'
UPDATE_TIMEZONE_PATH = 'api/auth/timezone/'
REGISTER_NAME = 'auth_register'
TOKEN_OBTAIN_NAME = 'auth_token_obtain_pair'
TOKEN_REFRESH_NAME = 'auth_token_refresh'
UPDATE_LANGUAGE_NAME = 'auth_update_language'
UPDATE_TIMEZONE_NAME = 'auth_update_timezone'

REGISTER_ACTION_MAP = {'post': 'create'}

POSTS_ROUTER_PREFIX = 'api/posts'
COMMENTS_ROUTER_PREFIX = 'comments'

router = DefaultRouter()
router.register(POSTS_ROUTER_PREFIX, PostViewSet, basename='post')

posts_router = NestedDefaultRouter(router, POSTS_ROUTER_PREFIX, lookup='post')
posts_router.register(COMMENTS_ROUTER_PREFIX, CommentViewSet, basename='post-comments')

urlpatterns = [
    path(ADMIN_PATH, admin.site.urls),
    path(
        REGISTER_PATH,
        RegisterViewSet.as_view(REGISTER_ACTION_MAP),
        name=REGISTER_NAME,
    ),
    path(TOKEN_OBTAIN_PATH, TokenObtainPairView.as_view(), name=TOKEN_OBTAIN_NAME),
    path(TOKEN_REFRESH_PATH, TokenRefreshView.as_view(), name=TOKEN_REFRESH_NAME),
    path(
        UPDATE_LANGUAGE_PATH,
        UpdateLanguageAPIView.as_view(),
        name=UPDATE_LANGUAGE_NAME,
    ),
    path(
        UPDATE_TIMEZONE_PATH,
        UpdateTimezoneAPIView.as_view(),
        name=UPDATE_TIMEZONE_NAME,
    ),
    path('', include(router.urls)),
    path('', include(posts_router.urls)),
]
