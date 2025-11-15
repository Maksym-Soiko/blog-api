from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
	def get_post_count(self):
		return self.posts.count()


class Category(models.Model):
	name = models.CharField(max_length=60, verbose_name='Назва категорії')
	description = models.TextField(verbose_name='Опис категорії')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')


class Post(models.Model):
	title = models.CharField(max_length=200, verbose_name='Заголовок статті')
	author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name='Автор')
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts', verbose_name='Категорія')
	content = models.TextField(verbose_name='Вміст статті')
	excerpt = models.CharField(max_length=300, verbose_name='Короткий опис')
	featured_image = models.ImageField(upload_to='post_images/', null=True, blank=True, verbose_name='Головне зображення')
	status = models.CharField(choices=[('draft', 'Чернетка'), ('published', 'Опубліковано')], default='draft', verbose_name='Статус')
	views = models.PositiveIntegerField(default=0, verbose_name='Кількість переглядів')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')
	updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата оновлення')
	published_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата публікації')

	class Meta:
		ordering = ['-published_at']
		verbose_name = 'Стаття'
		verbose_name_plural = 'Статті'

	def get_comment_count(self):
		return self.comments.filter(is_approved=True).count()
	
	def get_reading_time(self):
		words = len(self.content.split())
		reading_time_minutes = words // 200 + (1 if words % 200 > 0 else 0)
		return reading_time_minutes


class Comment(models.Model):
	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='Стаття')
	author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name='Автор коментаря')
	content = models.TextField(verbose_name='Текст коментаря')
	parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name='Батьківський коментар')
	is_approved = models.BooleanField(default=False, verbose_name='Схвалено')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')

	class Meta:
		ordering = ['created_at']
		verbose_name = 'Коментар'
		verbose_name_plural = 'Коментарі'