from django.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

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
    name = models.CharField(
        max_length=CATEGORY_NAME_MAX_LENGTH,
        unique=True,
        verbose_name=_('Category name (English)'),
    )
    name_ru = models.CharField(
        max_length=CATEGORY_NAME_MAX_LENGTH,
        default='',
        verbose_name=_('Category name (Russian)'),
    )
    name_kk = models.CharField(
        max_length=CATEGORY_NAME_MAX_LENGTH,
        default='',
        verbose_name=_('Category name (Kazakh)'),
    )
    slug = models.SlugField(unique=True, verbose_name=_('Category slug'))

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def localized_name(self) -> str:
        language = (get_language() or 'en').split('-', 1)[0]
        if language == 'ru' and self.name_ru:
            return self.name_ru
        if language == 'kk' and self.name_kk:
            return self.name_kk
        return self.name

    def __str__(self) -> str:
        return self.localized_name()


class Tag(models.Model):
    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        verbose_name=_('Tag name'),
    )
    slug = models.SlugField(unique=True, verbose_name=_('Tag slug'))

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

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
        verbose_name=_('Author'),
    )
    title = models.CharField(max_length=POST_TITLE_MAX_LENGTH, verbose_name=_('Title'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    body = models.TextField(verbose_name=_('Body'))
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name=CATEGORY_RELATED_NAME,
        verbose_name=_('Category'),
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name=TAGS_RELATED_NAME,
        verbose_name=_('Tags'),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_('Status'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name=POST_COMMENTS_RELATED_NAME,
        verbose_name=_('Post'),
    )
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name=AUTHOR_COMMENTS_RELATED_NAME,
        verbose_name=_('Author'),
    )
    body = models.TextField(verbose_name=_('Comment body'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self) -> str:
        return f'Comment {self.pk} on {self.post_id}'
