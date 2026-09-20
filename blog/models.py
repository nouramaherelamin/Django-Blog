from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=300, blank=True, help_text="Short description of the post")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_date']
        
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', args=[self.slug])
    
    def save(self, *args, **kwargs):
        if not self.excerpt:
            self.excerpt = self.content[:250] + "..."
        super().save(*args, **kwargs)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f'Comment by {self.name} on {self.post.title}'

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes_set')
    ip_address = models.GenericIPAddressField()
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'ip_address')
        
    def __str__(self):
        return f'Like on {self.post.title} by {self.ip_address}'