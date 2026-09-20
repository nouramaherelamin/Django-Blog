import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from blog.models import Post, Category

images = ['P1.jpg', 'P2.jpg', 'P3.jpg', 'P4.jpg', 'P5.jpg', 'P6.jpg', 'P7.jpg', 'P8.jpg', 'P9.jpg', 'P10.png']

category_image_map = {
    'Technology': ['P1.jpg', 'P4.jpg'],
    'Django': ['P1.jpg', 'P4.jpg'],
    'Travel': ['P2.jpg', 'P6.jpg', 'P9.jpg'],
    'Food': ['P3.jpg', 'P7.jpg'],
    'Lifestyle': ['P5.jpg', 'P8.jpg', 'P10.png'],
}

posts = Post.objects.all()
for post in posts:
    if post.category and post.category.name in category_image_map:
        image_name = random.choice(category_image_map[post.category.name])
    else:
        image_name = random.choice(images)
    
    post.image = f'post_images/{image_name}'
    post.save()
    print(f'Assigned {image_name} to {post.title}')

print('Done assigning images.')
