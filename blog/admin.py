from django.contrib import admin
from .models import User, Category, Post, Comment

class UserAdmin(admin.ModelAdmin):
	list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_post_count')
	list_filter = ('is_staff', 'is_superuser', 'is_active')
	search_fields = ('username', 'email', 'first_name', 'last_name')

	def get_post_count(self, obj):
		return obj.get_post_count()
	get_post_count.short_description = 'Кількість статей'


class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'description', 'created_at')
	list_filter = ('created_at',)
	search_fields = ('name',)


class PostAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'category', 'status', 'views', 'published_at', 'get_comment_count', 'get_reading_time')
	list_filter = ('status', 'category', 'author', 'published_at')
	search_fields = ('title', 'content', 'excerpt')
	date_hierarchy = 'published_at'
	ordering = ('-published_at',)

	def get_comment_count(self, obj):
		return obj.get_comment_count()
	get_comment_count.short_description = 'Кількість коментарів'

	def get_reading_time(self, obj):
		return f"{obj.get_reading_time()} хв"
	get_reading_time.short_description = 'Час читання'


class CommentAdmin(admin.ModelAdmin):
	list_display = ('post', 'author', 'is_approved', 'created_at')
	list_filter = ('is_approved', 'created_at')
	search_fields = ('content', 'author__username', 'post__title')
	date_hierarchy = 'created_at'


admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)