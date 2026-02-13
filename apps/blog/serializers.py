from rest_framework import serializers

from django.contrib.auth import get_user_model

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
    class Meta:
        model = Category
        fields = ('name', 'slug')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('name', 'slug')


class PostListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Post
        fields = ('slug', 'title', 'status', 'created_at', 'author')


class PostDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)

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
