from django.db import models

CATEGORY_NAME_MAX_LENGTH = 100
TAG_NAME_MAX_LENGTH = 50
POST_TITLE_MAX_LENGTH = 200

AUTHOR_RELATED_NAME = 'posts'
CATEGORY_RELATED_NAME = 'posts'
TAGS_RELATED_NAME = 'posts'
POST_COMMENTS_RELATED_NAME = 'comments'
AUTHOR_COMMENTS_RELATED_NAME = 'comments'

DRAFT_STATUS = 'draft'
PUBLISHED_STATUS = 'published'


class Category(models.Model):
    name = models.CharField(max_length=CATEGORY_NAME_MAX_LENGTH, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=TAG_NAME_MAX_LENGTH, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = DRAFT_STATUS, 'Draft'
        PUBLISHED = PUBLISHED_STATUS, 'Published'

    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name=AUTHOR_RELATED_NAME,
    )
    title = models.CharField(max_length=POST_TITLE_MAX_LENGTH)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name=CATEGORY_RELATED_NAME,
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name=TAGS_RELATED_NAME)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name=POST_COMMENTS_RELATED_NAME,
    )
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name=AUTHOR_COMMENTS_RELATED_NAME,
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Comment {self.pk} on {self.post_id}'
