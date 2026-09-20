from django import template
from django.db.models import Count, Q
from django.utils import timezone
from django.core.cache import cache
from ..models import Post, Category

register = template.Library()

@register.inclusion_tag('blog/sidebar.html', takes_context=True)
def show_sidebar(context):
    request = context['request']
    
    # Get trending posts (cached for 1 hour)
    trending_posts = cache.get('trending_posts')
    if trending_posts is None:
        week_ago = timezone.now() - timezone.timedelta(days=7)
        trending_posts = Post.objects.select_related('author', 'category').filter(
            published=True,
            created_date__gte=week_ago
        ).annotate(
            comment_count=Count('comments', filter=Q(comments__active=True))
        ).filter(comment_count__gt=0).order_by('-comment_count')[:5]
        cache.set('trending_posts', trending_posts, 60 * 60)
    
    # Get categories with post counts (cached for 30 minutes)
    categories = cache.get('categories_with_counts')
    if categories is None:
        categories = Category.objects.annotate(
            post_count=Count('post', filter=Q(post__published=True))
        ).filter(post_count__gt=0).order_by('name')
        cache.set('categories_with_counts', categories, 30 * 60)
        
    # Recent posts
    recent_posts = cache.get('sidebar_recent_posts')
    if recent_posts is None:
        recent_posts = Post.objects.select_related('author').filter(
            published=True
        ).order_by('-created_date')[:5]
        cache.set('sidebar_recent_posts', recent_posts, 15 * 60)
        
    # Archives (Group by year and month)
    archives = cache.get('sidebar_archives')
    if archives is None:
        # Get all distinct months and years with published posts
        posts = Post.objects.filter(published=True)
        dates = posts.dates('created_date', 'month', order='DESC')
        archives = []
        for d in dates:
            archives.append({
                'year': d.year,
                'month': d.month,
                'date': d
            })
        cache.set('sidebar_archives', archives, 60 * 60 * 12)
        
    return {
        'trending_posts': trending_posts,
        'categories': categories,
        'recent_posts': recent_posts,
        'archives': archives,
        'request': request,
    }
