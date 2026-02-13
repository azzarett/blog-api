# pyright: reportIncompatibleMethodOverride=false

from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.db.models import Q

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
            raise NotFound('Post not found.') from exc

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
