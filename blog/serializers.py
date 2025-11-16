from rest_framework import serializers
from .models import User, Post, Category, Comment
from django.db.models import Count, Sum

def _get_related_count(obj, attr_name, fallback_qs_func=None):
    rel = getattr(obj, attr_name, None)
    if rel is not None:
        try:
            return rel.count() if hasattr(rel, 'count') else len(rel)
        except Exception:
            pass
    if fallback_qs_func:
        try:
            return int(fallback_qs_func(obj)) or 0
        except Exception:
            return 0
    return 0


class UserSerializer(serializers.ModelSerializer):
    bio = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.SerializerMethodField(read_only=True)
    posts_count = serializers.SerializerMethodField(read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'bio', 'avatar', 'posts_count', 'full_name']

    def get_bio(self, obj):
        if getattr(obj, 'bio', None):
            return obj.bio
        profile = getattr(obj, 'profile', None)
        if profile and getattr(profile, 'bio', None):
            return profile.bio
        return None

    def get_avatar(self, obj):
        avatar = getattr(obj, 'avatar', None)
        if avatar:
            try:
                return avatar.url
            except Exception:
                return str(avatar)
        profile = getattr(obj, 'profile', None)
        if profile:
            avatar = getattr(profile, 'avatar', None)
            if avatar:
                try:
                    return avatar.url
                except Exception:
                    return str(avatar)
        return None

    def get_posts_count(self, obj):
        return _get_related_count(obj, 'posts', lambda o: Post.objects.filter(author=o).count())

    def get_full_name(self, obj):
        first = (getattr(obj, 'first_name', '') or '').strip()
        last = (getattr(obj, 'last_name', '') or '').strip()
        full = ' '.join(filter(None, [first, last]))
        if full:
            return full
        return getattr(obj, 'username', None)

    def validate_email(self, value):
        if not value:
            return value
        qs = User.objects.filter(email__iexact=value)
        instance = getattr(self, 'instance', None)
        if instance is not None:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Цей email вже використовується.")
        return value


class CategorySerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ['name', 'description', 'posts_count']

    def get_posts_count(self, obj):
        return _get_related_count(
            obj,
            'posts',
            lambda o: Post.objects.filter(category=o).count() if hasattr(Post, 'objects') else 0
        )


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'parent', 'is_approved', 'created_at', 'replies']
        read_only_fields = ['author', 'created_at']

    def get_replies(self, obj):
        qs = getattr(obj, 'replies', None)
        if not qs:
            return []
        depth = int(self.context.get('comment_depth', 3))
        if depth <= 0:
            return []
        try:
            new_context = dict(self.context, comment_depth=depth - 1)
            return CommentSerializer(qs.all(), many=True, context=new_context).data
        except Exception:
            try:
                return [
                    {
                        'id': c.pk,
                        'author': getattr(c.author, 'username', None),
                        'content': c.content,
                        'created_at': c.created_at,
                    }
                    for c in qs.all()
                ]
            except Exception:
                return []


class PostValidationMixin:
    def validate_title(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Заголовок повинен містити мінімум 10 символів.")
        return value

    def validate_content(self, value):
        if not value or len(value.strip()) < 100:
            raise serializers.ValidationError("Вміст статті повинен містити мінімум 100 символів.")
        return value


class PostListSerializer(PostValidationMixin, serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    reading_time = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'excerpt', 'author', 'category', 'featured_image', 'status', 'views', 'published_at', 'reading_time', 'comments_count']
        read_only_fields = ['author', 'views', 'created_at', 'updated_at', 'published_at']

    def get_reading_time(self, obj):
        try:
            return obj.get_reading_time()
        except Exception:
            content = getattr(obj, 'content', '') or ''
            words = len(content.split())
            return words // 200 + (1 if words % 200 > 0 else 0)

    def get_comments_count(self, obj):
        try:
            return obj.get_comment_count()
        except Exception:
            rel = getattr(obj, 'comments', None)
            if rel is not None:
                return rel.filter(is_approved=True).count()
            return 0


class PostDetailSerializer(PostValidationMixin, serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    reading_time = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    tags = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'excerpt', 'author', 'category', 'tags', 'featured_image', 'status', 'views', 'published_at', 'reading_time', 'comments_count', 'comments', 'created_at', 'updated_at']
        read_only_fields = ['author', 'views', 'created_at', 'updated_at', 'published_at']

    def get_tags(self, obj):
        tags_attr = getattr(obj, 'tags', None)
        if tags_attr is None:
            return []
        try:
            return [getattr(t, 'name', str(t)) for t in tags_attr.all()]
        except Exception:
            try:
                return list(tags_attr)
            except Exception:
                return []

    def get_reading_time(self, obj):
        try:
            return obj.get_reading_time()
        except Exception:
            content = getattr(obj, 'content', '') or ''
            words = len(content.split())
            return words // 200 + (1 if words % 200 > 0 else 0)

    def get_comments_count(self, obj):
        try:
            return obj.get_comment_count()
        except Exception:
            rel = getattr(obj, 'comments', None)
            if rel is not None:
                return rel.filter(is_approved=True).count()
            return 0


class BlogStatisticsSerializer(serializers.Serializer):
    total_posts = serializers.SerializerMethodField()
    published_posts = serializers.SerializerMethodField()
    drafts_count = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    top_posts = serializers.SerializerMethodField()
    top_authors = serializers.SerializerMethodField()

    def get_total_posts(self, obj):
        return Post.objects.count()

    def get_published_posts(self, obj):
        try:
            return Post.objects.filter(published_at__isnull=False).count()
        except Exception:
            try:
                return Post.objects.filter(status__iexact='published').count()
            except Exception:
                return 0

    def get_drafts_count(self, obj):
        return max(self.get_total_posts(obj) - self.get_published_posts(obj), 0)

    def get_total_comments(self, obj):
        return Comment.objects.count()

    def get_total_views(self, obj):
        return Post.objects.aggregate(total=Sum('views'))['total'] or 0

    def get_top_posts(self, obj):
        qs = Post.objects.order_by('-views')[:5]
        return PostListSerializer(qs, many=True, context=self.context).data

    def get_top_authors(self, obj):
        authors_agg = (
            Post.objects.values('author')
            .annotate(posts_count=Count('id'))
            .order_by('-posts_count')[:3]
        )
        author_ids = [a['author'] for a in authors_agg if a.get('author') is not None]
        users = {u.id: u for u in User.objects.filter(id__in=author_ids)}
        result = []
        for a in authors_agg:
            au_id = a.get('author')
            user = users.get(au_id)
            result.append({
                'author': UserSerializer(user, context=self.context).data if user else None,
                'posts_count': int(a.get('posts_count', 0))
            })
        return result


class CategoryStatisticsSerializer(serializers.Serializer):
    category = CategorySerializer(read_only=True)
    posts_count = serializers.IntegerField()
    total_views = serializers.IntegerField()
    avg_comments_per_post = serializers.FloatField()

    def to_representation(self, obj):
        category = obj
        category_data = CategorySerializer(category, context=self.context).data

        posts_qs = Post.objects.filter(category=category)
        posts_count = posts_qs.count()
        total_views = posts_qs.aggregate(total=Sum('views'))['total'] or 0
        total_comments = Comment.objects.filter(post__category=category).count()
        avg_comments = round(total_comments / posts_count, 2) if posts_count > 0 else 0.0

        return {
            'category': category_data,
            'posts_count': int(posts_count),
            'total_views': int(total_views),
            'avg_comments_per_post': float(avg_comments),
        }