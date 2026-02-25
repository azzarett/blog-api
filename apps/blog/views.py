# pyright: reportIncompatibleMethodOverride=false

import hashlib

from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.core.cache import cache
from django.db.models import Q
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from apps.blog.models import Comment, Post
from apps.blog.permissions import IsAuthorOrReadOnly
from apps.blog.serializers import (
    CommentSerializer,
    CommentWriteSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostWriteSerializer,
)

LIST_ACTION = 'list'
RETRIEVE_ACTION = 'retrieve'
CREATE_ACTION = 'create'
UPDATE_ACTION = 'update'
PARTIAL_UPDATE_ACTION = 'partial_update'
DESTROY_ACTION = 'destroy'

POST_LOOKUP_KWARG = 'post_slug'

WRITE_ACTIONS = {
    CREATE_ACTION,
    UPDATE_ACTION,
    PARTIAL_UPDATE_ACTION,
    DESTROY_ACTION,
}
POSTS_LIST_CACHE_VERSION_KEY = 'posts:list:version'
POSTS_LIST_CACHE_TIMEOUT_SECONDS = 300


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related(
        'author',
        'category',
    ).prefetch_related('tags')
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = self.queryset

        if self.action == LIST_ACTION:
            return queryset.filter(status=Post.Status.PUBLISHED)

        if self.action == RETRIEVE_ACTION:
            if self.request.user.is_authenticated:
                return queryset.filter(
                    Q(status=Post.Status.PUBLISHED) | Q(author=self.request.user)
                )
            return queryset.filter(status=Post.Status.PUBLISHED)

        return queryset

    def get_serializer_class(self):
        if self.action == LIST_ACTION:
            return PostListSerializer
        if self.action in {CREATE_ACTION, UPDATE_ACTION, PARTIAL_UPDATE_ACTION}:
            return PostWriteSerializer
        return PostDetailSerializer

    def list(self, request, *args, **kwargs) -> Response:
        cache_key = self._build_posts_list_cache_key(request)
        cached_payload = cache.get(cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=POSTS_LIST_CACHE_TIMEOUT_SECONDS)
        return response

    def _build_posts_list_cache_key(self, request) -> str:
        language = (get_language() or 'en').split('-', 1)[0]
        timezone_name = 'utc'
        if request.user.is_authenticated and getattr(request.user, 'timezone', None):
            timezone_name = request.user.timezone

        cache_version = cache.get(POSTS_LIST_CACHE_VERSION_KEY, 1)
        query_string = request.META.get('QUERY_STRING', '')
        query_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()

        return (
            f'posts:list:v{cache_version}:lang:{language}:'
            f'tz:{timezone_name}:q:{query_hash}'
        )

    def perform_create(self, serializer) -> None:
        serializer.save(author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    lookup_field = 'pk'

    def get_permissions(self):
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return [AllowAny()]

    def _get_visible_post(self) -> Post:
        post_slug = self.kwargs[POST_LOOKUP_KWARG]
        queryset = Post.objects.all()

        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(status=Post.Status.PUBLISHED) | Q(author=self.request.user)
            )
        else:
            queryset = queryset.filter(status=Post.Status.PUBLISHED)

        try:
            return queryset.get(slug=post_slug)
        except Post.DoesNotExist as exc:
            raise NotFound(_('Post not found.')) from exc

    def get_queryset(self):
        post = self._get_visible_post()
        return Comment.objects.select_related('author', 'post').filter(post=post)

    def get_serializer_class(self):
        if self.action in {CREATE_ACTION, UPDATE_ACTION, PARTIAL_UPDATE_ACTION}:
            return CommentWriteSerializer
        return CommentSerializer

    def perform_create(self, serializer) -> None:
        post = self._get_visible_post()
        serializer.save(author=self.request.user, post=post)
