from zoneinfo import ZoneInfo

from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.utils import formats, timezone

from apps.blog.models import Category, Comment, Post, Tag

User = get_user_model()

EMAIL_FIELD = 'email'
FIRST_NAME_FIELD = 'first_name'
LAST_NAME_FIELD = 'last_name'


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (EMAIL_FIELD, FIRST_NAME_FIELD, LAST_NAME_FIELD)


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('name', 'slug')

    def get_name(self, obj: Category) -> str:
        return obj.localized_name()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('name', 'slug')


class PostListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ('slug', 'title', 'status', 'created_at', 'updated_at', 'author')

    def get_created_at(self, obj: Post) -> str:
        return self._format_datetime(obj.created_at)

    def get_updated_at(self, obj: Post) -> str:
        return self._format_datetime(obj.updated_at)

    def _format_datetime(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if user and user.is_authenticated and getattr(user, 'timezone', None):
            target_timezone = ZoneInfo(user.timezone)
        else:
            target_timezone = ZoneInfo('UTC')

        localized_value = timezone.localtime(value, target_timezone)
        return formats.date_format(localized_value, 'j F Y H:i', use_l10n=True)


class PostDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'slug',
            'title',
            'body',
            'status',
            'category',
            'tags',
            'created_at',
            'updated_at',
            'author',
        )

    def get_created_at(self, obj: Post) -> str:
        return self._format_datetime(obj.created_at)

    def get_updated_at(self, obj: Post) -> str:
        return self._format_datetime(obj.updated_at)

    def _format_datetime(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if user and user.is_authenticated and getattr(user, 'timezone', None):
            target_timezone = ZoneInfo(user.timezone)
        else:
            target_timezone = ZoneInfo('UTC')

        localized_value = timezone.localtime(value, target_timezone)
        return formats.date_format(localized_value, 'j F Y H:i', use_l10n=True)


class PostWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
    )
    tags = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Post
        fields = ('title', 'slug', 'body', 'category', 'tags', 'status')


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'body', 'created_at', 'author')


class CommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('body',)
