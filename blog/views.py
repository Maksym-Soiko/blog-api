from rest_framework.response import Response
from .models import User, Post, Category, Comment
from .serializers import (
    UserSerializer, PostListSerializer, PostDetailSerializer,
    CategorySerializer, CommentSerializer, BlogStatisticsSerializer, CategoryStatisticsSerializer
)
from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class PostListAPIView(generics.ListAPIView):
	queryset = Post.objects.select_related('author', 'category').order_by('-published_at')
	serializer_class = PostListSerializer
	permission_classes = [AllowAny]

class PostDetailAPIView(generics.RetrieveAPIView):
	queryset = Post.objects.all()
	serializer_class = PostDetailSerializer
	lookup_field = 'id'
	permission_classes = [AllowAny]

class PostCommentListAPIView(generics.ListAPIView):
	serializer_class = CommentSerializer
	permission_classes = [AllowAny]

	def get_queryset(self):
		post_id = self.kwargs['post_id']
		return Comment.objects.filter(post__id=post_id)
	
class CategoryListAPIView(generics.ListAPIView):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer
	permission_classes = [AllowAny]

class CategoryPostListAPIView(generics.ListAPIView):
	serializer_class = PostListSerializer
	permission_classes = [AllowAny]

	def get_queryset(self):
		category_id = self.kwargs['category_id']
		return Post.objects.filter(category__id=category_id)

class AuthorListAPIView(generics.ListAPIView):
	serializer_class = UserSerializer
	permission_classes = [AllowAny]

	def get_queryset(self):
		return User.objects.filter(posts__isnull=False).distinct().order_by('username')

class AuthorPostsAPIView(generics.ListAPIView):
	serializer_class = PostListSerializer
	permission_classes = [AllowAny]

	def get_queryset(self):
		author_id = self.kwargs.get('pk') or self.kwargs.get('author_id')
		get_object_or_404(User, pk=author_id)
		return Post.objects.filter(author_id=author_id).select_related('author', 'category').order_by('-published_at')

class MyPostsAPIView(generics.ListAPIView):
	serializer_class = PostListSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		return Post.objects.filter(author=user).select_related('author', 'category').order_by('-published_at')

class BlogStatisticsAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request, *args, **kwargs):
		serializer = BlogStatisticsSerializer(instance=object(), context={'request': request})
		return Response(serializer.data)

class CategoryStatisticsAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request, category_id, *args, **kwargs):
		category = get_object_or_404(Category, pk=category_id)
		serializer = CategoryStatisticsSerializer(instance=category, context={'request': request})
		return Response(serializer.data)

@method_decorator(cache_page(60 * 5), name='dispatch')
class PopularPostsAPIView(generics.ListAPIView):
	serializer_class = PostListSerializer
	permission_classes = [AllowAny]

	def get_queryset(self):
		qs = Post.objects.select_related('author', 'category')
		try:
			qs = qs.filter(published_at__isnull=False)
		except Exception:
			qs = qs.filter(status__iexact='published')
		return qs.order_by('-views')[:5]