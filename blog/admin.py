from django.contrib import admin
from django.utils.html import format_html
from .models import Post, Category, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_date', 'post_count']
    search_fields = ['name']
    readonly_fields = ['created_date']
    
    def post_count(self, obj):
        return obj.post_set.count()
    post_count.short_description = 'Number of Posts'

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'published', 'featured', 'created_date']
    list_filter = ['published', 'featured', 'category', 'created_date']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_date'
    ordering = ['-created_date']
    
    fieldsets = (
        ('Post Information', {
            'fields': ('title', 'slug', 'author', 'category')
        }),
        ('Content', {
            'fields': ('excerpt', 'content')
        }),
        ('Settings', {
            'fields': ('published', 'featured')
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'post', 'created_date', 'active']
    list_filter = ['active', 'created_date']
    search_fields = ['name', 'content']
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        queryset.update(active=True)
    make_active.short_description = "Mark selected comments as active"
    
    def make_inactive(self, request, queryset):
        queryset.update(active=False)
    make_inactive.short_description = "Mark selected comments as inactive"