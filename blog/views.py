from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.db.models import Q, Count, F
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import json
from .models import Post, Category, Comment, Like
from .forms import CommentForm

def home(request):
    """Enhanced home page with latest posts, trending, and better search"""
    # Base queryset with optimizations
    posts = Post.objects.select_related('author', 'category').filter(published=True)
    
    # Get featured posts (cached for 15 minutes)
    featured_posts = cache.get('featured_posts')
    if featured_posts is None:
        featured_posts = Post.objects.select_related('author', 'category').filter(
            published=True, featured=True
        ).order_by('-created_date')[:3]
        cache.set('featured_posts', featured_posts, 15 * 60)
    
    # Get categories with post counts (cached for 30 minutes)
    categories = cache.get('categories_with_counts')
    if categories is None:
        categories = Category.objects.annotate(
            post_count=Count('post', filter=Q(post__published=True))
        ).filter(post_count__gt=0).order_by('name')
        cache.set('categories_with_counts', categories, 30 * 60)
    
    # Enhanced search functionality
    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category')
    sort_by = request.GET.get('sort', 'newest')  # newest, oldest, popular, title
    
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(author__username__icontains=search_query)
        ).distinct()
    
    # Category filtering
    if category_filter and category_filter.isdigit():
        posts = posts.filter(category_id=category_filter)
        selected_category = get_object_or_404(Category, id=category_filter)
    else:
        selected_category = None
    
    # Sorting options
    if sort_by == 'oldest':
        posts = posts.order_by('created_date')
    elif sort_by == 'popular':
        posts = posts.annotate(
            comment_count=Count('comments', filter=Q(comments__active=True))
        ).order_by('-comment_count', '-created_date')
    elif sort_by == 'title':
        posts = posts.order_by('title')
    else:  # newest (default)
        posts = posts.order_by('-created_date')
    
    # Enhanced pagination with error handling
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get trending posts (most commented in last 7 days)
    trending_posts = cache.get('trending_posts')
    if trending_posts is None:
        week_ago = timezone.now() - timezone.timedelta(days=7)
        trending_posts = Post.objects.select_related('author', 'category').filter(
            published=True,
            created_date__gte=week_ago
        ).annotate(
            comment_count=Count('comments', filter=Q(comments__active=True))
        ).filter(comment_count__gt=0).order_by('-comment_count')[:5]
        cache.set('trending_posts', trending_posts, 60 * 60)  # 1 hour cache
    
    # Recent posts for sidebar
    recent_posts = Post.objects.select_related('author').filter(
        published=True
    ).exclude(featured=True).order_by('-created_date')[:5]
    
    # Site-wide stats for Hero section
    from django.db.models import Sum
    total_site_views = Post.objects.aggregate(Sum('views_count'))['views_count__sum'] or 0
    total_site_posts = Post.objects.filter(published=True).count()
    total_site_categories = Category.objects.count()

    context = {
        'page_obj': page_obj,
        'featured_posts': featured_posts,
        'trending_posts': trending_posts,
        'recent_posts': recent_posts,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_posts': paginator.count,
        'has_filters': bool(search_query or category_filter),
        'total_site_views': total_site_views,
        'total_site_posts': total_site_posts,
        'total_site_categories': total_site_categories,
    }
    return render(request, 'blog/home.html', context)

def post_detail(request, slug):
    """Enhanced post detail page with view tracking and better related posts"""
    # Get post with related data
    post = get_object_or_404(
        Post.objects.select_related('author', 'category').prefetch_related(
            'comments__author' if hasattr(Comment, 'author') else 'comments'
        ),
        slug=slug,
        published=True
    )
    
    # Track post views using session/cache to prevent refresh spam
    user_ip = get_client_ip(request)
    view_key = f'viewed_post_{post.id}_{user_ip}'
    if not cache.get(view_key):
        Post.objects.filter(id=post.id).update(views_count=F('views_count') + 1)
        post.refresh_from_db(fields=['views_count'])
        cache.set(view_key, True, 60 * 60 * 2)  # 2 hours timeout per IP
    
    # Get active comments with better ordering
    comments = post.comments.filter(active=True).order_by('-created_date')
    
    # Handle comment form with better validation
    comment_form = CommentForm()
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            # Check for spam (simple rate limiting)
            user_ip = get_client_ip(request)
            recent_comments_key = f'comments_{user_ip}'
            recent_comments = cache.get(recent_comments_key, 0)
            
            if recent_comments >= 3:  # Max 3 comments per IP per hour
                messages.error(request, 'You have reached the comment limit. Please try again later.')
            else:
                comment = comment_form.save(commit=False)
                comment.post = post
                comment.save()
                
                # Update rate limiting counter
                cache.set(recent_comments_key, recent_comments + 1, 60 * 60)
                
                messages.success(request, 'Your comment has been added successfully!')
                return redirect('blog:post_detail', slug=slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    
    # Enhanced related posts algorithm
    related_posts = []
    if post.category:
        # First try: same category, exclude current post
        related_posts = list(Post.objects.select_related('author', 'category').filter(
            category=post.category,
            published=True
        ).exclude(id=post.id).order_by('-created_date')[:3])
    
    # If not enough related posts, get recent posts from other categories
    if len(related_posts) < 3:
        additional_posts = Post.objects.select_related('author', 'category').filter(
            published=True
        ).exclude(id=post.id).exclude(
            id__in=[p.id for p in related_posts]
        ).order_by('-created_date')[:3 - len(related_posts)]
        related_posts.extend(list(additional_posts))
    
    # Get previous and next posts
    try:
        previous_post = Post.objects.filter(
            published=True,
            created_date__lt=post.created_date
        ).order_by('-created_date').first()
    except Post.DoesNotExist:
        previous_post = None
    
    try:
        next_post = Post.objects.filter(
            published=True,
            created_date__gt=post.created_date
        ).order_by('created_date').first()
    except Post.DoesNotExist:
        next_post = None
    
    # Reading time estimation (average 200 words per minute)
    word_count = len(post.content.split())
    reading_time = max(1, round(word_count / 200))
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'related_posts': related_posts,
        'previous_post': previous_post,
        'next_post': next_post,
        'view_count': post.views_count,
        'reading_time': reading_time,
        'word_count': word_count,
        'comment_count': comments.count(),
        'like_count': post.likes_set.count(),
        'user_has_liked': post.likes_set.filter(ip_address=get_client_ip(request)).exists(),
    }
    return render(request, 'blog/post_detail.html', context)

def category_posts(request, category_id):
    """Enhanced category posts page with better filtering and stats"""
    category = get_object_or_404(Category, id=category_id)
    
    # Get posts with optimized query
    posts = Post.objects.select_related('author').filter(
        category=category, 
        published=True
    )
    
    # Sorting options for category page
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        posts = posts.order_by('created_date')
    elif sort_by == 'popular':
        posts = posts.annotate(
            comment_count=Count('comments', filter=Q(comments__active=True))
        ).order_by('-comment_count', '-created_date')
    elif sort_by == 'title':
        posts = posts.order_by('title')
    else:  # newest (default)
        posts = posts.order_by('-created_date')
    
    # Enhanced pagination
    paginator = Paginator(posts, 9)  # More posts per page for category view
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    # Category statistics
    total_posts = posts.count()
    recent_posts = posts.order_by('-created_date')[:3]
    
    # Get other categories for sidebar
    other_categories = Category.objects.exclude(id=category_id).annotate(
        post_count=Count('post', filter=Q(post__published=True))
    ).filter(post_count__gt=0)[:6]
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'recent_posts': recent_posts,
        'other_categories': other_categories,
        'total_posts': total_posts,
        'sort_by': sort_by,
    }
    return render(request, 'blog/category_posts.html', context)

def about(request):
    """Enhanced about page with site statistics"""
    # Get site statistics
    stats = cache.get('site_stats')
    if stats is None:
        from django.db.models import Sum
        total_views = Post.objects.aggregate(Sum('views_count'))['views_count__sum'] or 0
        stats = {
            'total_posts': Post.objects.filter(published=True).count(),
            'total_categories': Category.objects.count(),
            'total_comments': Comment.objects.filter(active=True).count(),
            'total_views': total_views,
            'latest_post': Post.objects.filter(published=True).order_by('-created_date').first(),
        }
        cache.set('site_stats', stats, 60 * 60)  # 1 hour cache
    
    context = {
        'stats': stats,
        'site_info': {
            'name': getattr(settings, 'SITE_NAME', 'My Blog'),
            'description': getattr(settings, 'SITE_DESCRIPTION', 'A Django-powered blog'),
            'version': '1.0',
        }
    }
    return render(request, 'blog/about.html', context)

def explore(request):
    posts = Post.objects.select_related('author', 'category').filter(
        published=True
    ).order_by('-created_date')

    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'total_posts': posts.count(),
    }

    return render(request, 'blog/explore.html', context)


def contact(request):
    return render(request, 'blog/contact.html')

# AJAX Views for enhanced functionality

@require_POST
def like_post(request, post_id):
    """AJAX view to like/unlike posts persistently"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        raise Http404()
    
    post = get_object_or_404(Post, id=post_id, published=True)
    user_ip = get_client_ip(request)
    
    like, created = Like.objects.get_or_create(post=post, ip_address=user_ip)
    
    if not created:
        # User already liked, so unlike
        like.delete()
        action = 'unliked'
    else:
        # Newly created like
        action = 'liked'
    
    current_likes = post.likes_set.count()
    
    return JsonResponse({
        'success': True,
        'action': action,
        'likes': current_likes
    })

def search_suggestions(request):
    """AJAX view for search autocomplete"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'suggestions': []})
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Search in post titles
    suggestions = Post.objects.filter(
        title__icontains=query,
        published=True
    ).values_list('title', flat=True)[:5]
    
    return JsonResponse({'suggestions': list(suggestions)})

def load_more_posts(request):
    """AJAX view for infinite scroll"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        raise Http404()
    
    page = request.GET.get('page', 1)
    category_id = request.GET.get('category')
    
    posts = Post.objects.select_related('author', 'category').filter(published=True)
    
    if category_id:
        posts = posts.filter(category_id=category_id)
    
    paginator = Paginator(posts, 6)
    
    try:
        page_obj = paginator.page(page)
        has_next = page_obj.has_next()
        
        posts_data = []
        for post in page_obj:
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'excerpt': post.excerpt,
                'author': post.author.username,
                'created_date': post.created_date.strftime('%B %d, %Y'),
                'category': post.category.name if post.category else None,
                'url': post.get_absolute_url(),
            })
        
        return JsonResponse({
            'success': True,
            'posts': posts_data,
            'has_next': has_next,
            'next_page': page_obj.next_page_number() if has_next else None
        })
    
    except (EmptyPage, PageNotAnInteger):
        return JsonResponse({'success': False, 'message': 'Invalid page'})

# Utility Functions

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Explore View

def explore(request):
    posts = Post.objects.select_related('author', 'category').filter(
        published=True
    ).order_by('-created_date')

    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'total_posts': posts.count(),
    }

    return render(request, 'blog/explore.html', context)


# Archive Views

def archive(request):
    posts = Post.objects.select_related('author', 'category').filter(
        published=True
    ).order_by('-created_date')

    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'archive_type': 'all',
    }

    return render(request, 'blog/archive.html', context)


# Contact View

def contact(request):
    return render(request, 'blog/contact.html')

def archive_year(request, year):
    """Posts archive by year"""
    posts = Post.objects.select_related('author', 'category').filter(
        created_date__year=year,
        published=True
    ).order_by('-created_date')
    
    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'year': year,
        'page_obj': page_obj,
        'archive_type': 'year'
    }
    return render(request, 'blog/archive.html', context)

def archive_month(request, year, month):
    """Posts archive by month"""
    posts = Post.objects.select_related('author', 'category').filter(
        created_date__year=year,
        created_date__month=month,
        published=True
    ).order_by('-created_date')
    
    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'year': year,
        'month': month,
        'page_obj': page_obj,
        'archive_type': 'month'
    }
    return render(request, 'blog/archive.html', context)

# Author profile view
def author_posts(request, username):
    """Posts by specific author"""
    from django.contrib.auth.models import User
    
    author = get_object_or_404(User, username=username)
    posts = Post.objects.select_related('category').filter(
        author=author,
        published=True
    ).order_by('-created_date')
    
    paginator = Paginator(posts, 8)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'author': author,
        'page_obj': page_obj,
        'total_posts': posts.count()
    }
    return render(request, 'blog/author_posts.html', context)