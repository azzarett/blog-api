# pyright: reportIncompatibleMethodOverride=false

import asyncio
import hashlib

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
import httpx
from asgiref.sync import sync_to_async

from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from apps.blog.models import Comment, Post
from apps.blog.permissions import IsAuthorOrReadOnly
from apps.blog.serializers import (
    CommentSerializer,
    CommentWriteSerializer,
    PaginatedCommentListSerializer,
    PaginatedPostListSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostWriteSerializer,
    StatsSerializer,
)
from apps.users.serializers import (
    ErrorDetailSerializer,
    MessageSerializer,
    ValidationErrorResponseSerializer,
)

User = get_user_model()

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


@extend_schema_view(
    list=extend_schema(
        tags=['Posts'],
        summary='List published posts',
        description=(
            'Returns paginated published posts for anonymous users and localizes '
            'fields according to active language/timezone. Anonymous users receive '
            'UTC timestamps. Side effects: reads and writes Redis cache using '\
            'language-aware keys.'
        ),
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Optional language override: en, ru, kk.',
            ),
            OpenApiParameter(
                name='page',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Pagination page number.',
            ),
        ],
        responses={
            200: PaginatedPostListSerializer,
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'List posts request',
                request_only=True,
                value={'lang': 'ru', 'page': 1},
            ),
            OpenApiExample(
                'List posts response',
                response_only=True,
                value={
                    'count': 1,
                    'next': None,
                    'previous': None,
                    'results': [
                        {
                            'slug': 'hello-world',
                            'title': 'Hello world',
                            'status': 'published',
                            'created_at': '25 февраля 2026 10:00',
                            'updated_at': '25 февраля 2026 11:00',
                            'author': {
                                'email': 'user@example.com',
                                'first_name': 'Azat',
                                'last_name': 'Bertaeyev',
                            },
                        }
                    ],
                },
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=['Posts'],
        summary='Retrieve post by slug',
        description=(
            'Returns post details by slug. Anonymous users can access published '
            'posts only; authenticated users can also access their own drafts. '
            'Localized category names and timezone-aware date formatting are applied.'
        ),
        responses={
            200: PostDetailSerializer,
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Retrieve post request',
                request_only=True,
                value={'slug': 'hello-world', 'lang': 'kk'},
            ),
            OpenApiExample(
                'Retrieve post response',
                response_only=True,
                value={
                    'slug': 'hello-world',
                    'title': 'Hello world',
                    'body': 'Post body',
                    'status': 'published',
                    'category': {'name': 'Технология', 'slug': 'tech'},
                    'tags': [{'name': 'django', 'slug': 'django'}],
                    'created_at': '25 February 2026 10:00',
                    'updated_at': '25 February 2026 11:00',
                    'author': {
                        'email': 'user@example.com',
                        'first_name': 'Azat',
                        'last_name': 'Bertaeyev',
                    },
                },
            ),
        ],
    ),
    create=extend_schema(
        tags=['Posts'],
        summary='Create a post',
        description=(
            'Creates a post for the authenticated user. Requires JWT auth. Side '
            'effects: invalidates cached post list for all languages/timezones via '
            'cache version bump in Redis.'
        ),
        request=PostWriteSerializer,
        responses={
            201: PostWriteSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            403: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Create post request',
                request_only=True,
                value={
                    'title': 'My post',
                    'slug': 'my-post',
                    'body': 'Text',
                    'category': 'tech',
                    'tags': ['django'],
                    'status': 'draft',
                },
            ),
            OpenApiExample(
                'Create post response',
                response_only=True,
                value={
                    'title': 'My post',
                    'slug': 'my-post',
                    'body': 'Text',
                    'category': 'tech',
                    'tags': ['django'],
                    'status': 'draft',
                },
            ),
        ],
    ),
    update=extend_schema(
        tags=['Posts'],
        summary='Replace a post',
        description=(
            'Fully updates a post by slug. Requires JWT auth and ownership. Side '
            'effect: invalidates Redis cached list for all languages/timezones.'
        ),
        request=PostWriteSerializer,
        responses={
            200: PostWriteSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            403: OpenApiResponse(response=ErrorDetailSerializer),
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Update post request',
                request_only=True,
                value={
                    'title': 'Updated title',
                    'slug': 'my-post',
                    'body': 'Updated text',
                    'category': 'tech',
                    'tags': ['django'],
                    'status': 'published',
                },
            ),
            OpenApiExample(
                'Update post response',
                response_only=True,
                value={
                    'title': 'Updated title',
                    'slug': 'my-post',
                    'body': 'Updated text',
                    'category': 'tech',
                    'tags': ['django'],
                    'status': 'published',
                },
            ),
        ],
    ),
    partial_update=extend_schema(
        tags=['Posts'],
        summary='Partially update a post',
        description=(
            'Partially updates a post by slug. Requires JWT auth and ownership. Side '
            'effect: invalidates Redis cached list for all languages/timezones.'
        ),
        request=PostWriteSerializer,
        responses={
            200: PostWriteSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            403: OpenApiResponse(response=ErrorDetailSerializer),
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Partial update request',
                request_only=True,
                value={'status': 'published'},
            ),
            OpenApiExample(
                'Partial update response',
                response_only=True,
                value={
                    'title': 'Updated title',
                    'slug': 'my-post',
                    'body': 'Updated text',
                    'category': 'tech',
                    'tags': ['django'],
                    'status': 'published',
                },
            ),
        ],
    ),
    destroy=extend_schema(
        tags=['Posts'],
        summary='Delete a post',
        description=(
            'Deletes a post by slug. Requires JWT auth and ownership. Side effect: '
            'invalidates Redis cached list for all languages/timezones.'
        ),
        responses={
            204: OpenApiResponse(description='Post deleted successfully.'),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            403: OpenApiResponse(response=ErrorDetailSerializer),
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Delete post request',
                request_only=True,
                value={'slug': 'my-post'},
            ),
            OpenApiExample(
                'Delete post response',
                response_only=True,
                value=None,
            ),
        ],
    ),
)
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


@extend_schema_view(
    list=extend_schema(
        tags=['Comments'],
        summary='List comments for a post',
        description=(
            'Returns paginated comments for a visible post. Anonymous users can view '
            'comments for published posts; authenticated users can also see comments '
            'for their own draft posts.'
        ),
        parameters=[
            OpenApiParameter(
                name='post_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Slug of parent post.',
            ),
        ],
        responses={
            200: PaginatedCommentListSerializer,
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'List comments request',
                request_only=True,
                value={'post_slug': 'hello-world'},
            ),
            OpenApiExample(
                'List comments response',
                response_only=True,
                value={
                    'count': 1,
                    'next': None,
                    'previous': None,
                    'results': [
                        {
                            'id': 1,
                            'body': 'Great post!',
                            'created_at': '2026-02-25T11:00:00Z',
                            'author': {
                                'email': 'user@example.com',
                                'first_name': 'Azat',
                                'last_name': 'Bertaeyev',
                            },
                        }
                    ],
                },
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=['Comments'],
        summary='Retrieve comment by id',
        description='Returns a single comment for the specified parent post and id.',
        parameters=[
            OpenApiParameter(
                name='post_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Slug of parent post.',
            ),
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description='Comment identifier.',
            ),
        ],
        responses={
            200: CommentSerializer,
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Retrieve comment request',
                request_only=True,
                value={'post_slug': 'hello-world', 'id': 1},
            ),
            OpenApiExample(
                'Retrieve comment response',
                response_only=True,
                value={
                    'id': 1,
                    'body': 'Great post!',
                    'created_at': '2026-02-25T11:00:00Z',
                    'author': {
                        'email': 'user@example.com',
                        'first_name': 'Azat',
                        'last_name': 'Bertaeyev',
                    },
                },
            ),
        ],
    ),
    create=extend_schema(
        tags=['Comments'],
        summary='Create a comment',
        description='Creates a comment for a post. Requires JWT authentication.',
        parameters=[
            OpenApiParameter(
                name='post_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Slug of parent post.',
            ),
        ],
        request=CommentWriteSerializer,
        responses={
            201: CommentWriteSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            403: OpenApiResponse(response=ErrorDetailSerializer),
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Create comment request',
                request_only=True,
                value={'body': 'Great post!'},
            ),
            OpenApiExample(
                'Create comment response',
                response_only=True,
                value={'body': 'Great post!'},
            ),
        ],
    ),
    update=extend_schema(
        tags=['Comments'],
        summary='Replace a comment',
        description=(
            'Fully updates a comment. Requires JWT authentication and ownership.'
        ),
        parameters=[
            OpenApiParameter(
                name='post_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Slug of parent post.',
            ),
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description='Comment identifier.',
            ),
        ],
        request=CommentWriteSerializer,
        responses={
            200: CommentWriteSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            403: OpenApiResponse(response=ErrorDetailSerializer),
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Update comment request',
                request_only=True,
                value={'body': 'Updated comment'},
            ),
            OpenApiExample(
                'Update comment response',
                response_only=True,
                value={'body': 'Updated comment'},
            ),
        ],
    ),
    partial_update=extend_schema(
        tags=['Comments'],
        summary='Partially update a comment',
        description=(
            'Partially updates a comment. Requires JWT authentication and ownership.'
        ),
        parameters=[
            OpenApiParameter(
                name='post_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Slug of parent post.',
            ),
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description='Comment identifier.',
            ),
        ],
        request=CommentWriteSerializer,
        responses={
            200: CommentWriteSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            403: OpenApiResponse(response=ErrorDetailSerializer),
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Partial update comment request',
                request_only=True,
                value={'body': 'Short update'},
            ),
            OpenApiExample(
                'Partial update comment response',
                response_only=True,
                value={'body': 'Short update'},
            ),
        ],
    ),
    destroy=extend_schema(
        tags=['Comments'],
        summary='Delete a comment',
        description='Deletes a comment. Requires JWT authentication and ownership.',
        parameters=[
            OpenApiParameter(
                name='post_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Slug of parent post.',
            ),
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description='Comment identifier.',
            ),
        ],
        responses={
            204: OpenApiResponse(description='Comment deleted successfully.'),
            401: OpenApiResponse(response=ErrorDetailSerializer),
            403: OpenApiResponse(response=ErrorDetailSerializer),
            404: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Delete comment request',
                request_only=True,
                value={'post_slug': 'hello-world', 'id': 1},
            ),
            OpenApiExample(
                'Delete comment response',
                response_only=True,
                value=None,
            ),
        ],
    ),
)
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author', 'post')
    lookup_field = 'pk'
    lookup_url_kwarg = 'id'

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
        return self.queryset.filter(post=post)

    def get_serializer_class(self):
        if self.action in {CREATE_ACTION, UPDATE_ACTION, PARTIAL_UPDATE_ACTION}:
            return CommentWriteSerializer
        return CommentSerializer

    def perform_create(self, serializer) -> None:
        post = self._get_visible_post()
        serializer.save(author=self.request.user, post=post)


class StatsAPIView(APIView):
    permission_classes = (AllowAny,)

    EXCHANGE_RATES_URL = 'https://open.er-api.com/v6/latest/USD'
    ALMATY_TIME_URL = (
        'https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty'
    )
    HTTP_TIMEOUT_SECONDS = 10.0

    @extend_schema(
        tags=['Stats'],
        summary='Get blog and external statistics',
        description=(
            'Returns local blog counters together with exchange rates and current '
            'Almaty time from external public APIs. External requests are executed '
            'concurrently to reduce overall latency. Authentication is not required.'
        ),
        responses={
            200: StatsSerializer,
            503: OpenApiResponse(response=ErrorDetailSerializer),
            429: OpenApiResponse(response=MessageSerializer),
        },
        examples=[
            OpenApiExample(
                'Stats request',
                request_only=True,
                value={'lang': 'en'},
            ),
            OpenApiExample(
                'Stats response',
                response_only=True,
                value={
                    'blog': {
                        'total_posts': 42,
                        'total_comments': 137,
                        'total_users': 15,
                    },
                    'exchange_rates': {
                        'KZT': 450.23,
                        'RUB': 89.10,
                        'EUR': 0.92,
                    },
                    'current_time': '2024-03-15T18:30:00+05:00',
                },
            ),
        ],
    )
    async def get(self, request, *args, **kwargs) -> Response:
        # Async is used to overlap external HTTP I/O; synchronous calls would block
        # the request thread and increase end-to-end latency under load.
        try:
            exchange_rates, current_time = await self._fetch_external_data()
        except (httpx.HTTPError, KeyError, ValueError):
            return Response(
                {'detail': _('Failed to fetch external statistics.')}, status=503
            )

        total_posts, total_comments, total_users = await asyncio.gather(
            sync_to_async(Post.objects.count, thread_sensitive=True)(),
            sync_to_async(Comment.objects.count, thread_sensitive=True)(),
            sync_to_async(User.objects.count, thread_sensitive=True)(),
        )

        return Response(
            {
                'blog': {
                    'total_posts': total_posts,
                    'total_comments': total_comments,
                    'total_users': total_users,
                },
                'exchange_rates': exchange_rates,
                'current_time': current_time,
            }
        )

    async def _fetch_external_data(self) -> tuple[dict[str, float], str]:
        async with httpx.AsyncClient(timeout=self.HTTP_TIMEOUT_SECONDS) as client:
            exchange_response, time_response = await asyncio.gather(
                client.get(self.EXCHANGE_RATES_URL),
                client.get(self.ALMATY_TIME_URL),
            )

        exchange_response.raise_for_status()
        time_response.raise_for_status()

        exchange_payload = exchange_response.json()
        time_payload = time_response.json()

        rates = exchange_payload['rates']
        exchange_rates = {
            'KZT': float(rates['KZT']),
            'RUB': float(rates['RUB']),
            'EUR': float(rates['EUR']),
        }
        current_time = str(time_payload['dateTime'])

        return exchange_rates, current_time
