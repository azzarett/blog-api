from django.db import models

MAX_NAME_LENGTH = 255
MAX_TITLE_LENGTH = 255
POSTS_RELATED_NAME = 'posts'
COMMENTS_RELATED_NAME = 'comments'


class Category(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=MAX_TITLE_LENGTH)
    content = models.TextField()
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name=POSTS_RELATED_NAME,
    )
    categories = models.ManyToManyField(Category, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name=COMMENTS_RELATED_NAME,
    )
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name=COMMENTS_RELATED_NAME,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Comment {self.pk} on {self.post_id}'
