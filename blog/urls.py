from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('explore/', views.explore, name='explore'),
    path('contact/', views.contact, name='contact'),

    path('post/<slug:slug>/', views.post_detail, name='post_detail'),

    path('category/<int:category_id>/', views.category_posts, name='category_posts'),

    path('author/<str:username>/', views.author_posts, name='author_posts'),

    path('archive/', views.archive, name='archive'),
    path('archive/<int:year>/', views.archive_year, name='archive_year'),
    path('archive/<int:year>/<int:month>/', views.archive_month, name='archive_month'),

    path('ajax/like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('ajax/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('ajax/load-more-posts/', views.load_more_posts, name='load_more_posts'),
]