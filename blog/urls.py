from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
	path('posts/', views.PostListAPIView.as_view(), name='post_list'),
	path('posts/<int:id>/', views.PostDetailAPIView.as_view(), name='post_detail'),
	path('posts/<int:post_id>/comments/', views.PostCommentListAPIView.as_view(), name='post_comments'),
	path('categories/', views.CategoryListAPIView.as_view(), name='category_list'),
	path('categories/<int:category_id>/posts/', views.CategoryPostListAPIView.as_view(), name='category_posts'),
	path('categories/<int:category_id>/statistics/', views.CategoryStatisticsAPIView.as_view(), name='category_statistics'),
	path('authors/', views.AuthorListAPIView.as_view(), name='author_list'),
	path('authors/<int:author_id>/posts/', views.AuthorPostsAPIView.as_view(), name='author_posts'),
	path('my-posts/', views.MyPostsAPIView.as_view(), name='my_posts'),
	path('statistics/', views.BlogStatisticsAPIView.as_view(), name='blog_statistics'),
	path('popular/', views.PopularPostsAPIView.as_view(), name='popular_posts'),
]