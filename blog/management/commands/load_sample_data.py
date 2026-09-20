from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import Category, Post
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Load sample data for the blog'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {'name': 'Technology', 'description': 'Posts about technology and programming'},
            {'name': 'Travel', 'description': 'Travel experiences and tips'},
            {'name': 'Food', 'description': 'Recipes and food reviews'},
            {'name': 'Lifestyle', 'description': 'Lifestyle and personal development'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user')

        # Sample posts data
        posts_data = [
            {
                'title': 'Welcome to My Simple Blog',
                'content': '''Welcome to my simple Django blog! This is the first post on this blog platform.

This blog demonstrates various Django features including:
- Model relationships
- Template inheritance  
- Form handling
- Admin interface
- Search functionality

Feel free to explore the different features and leave comments on posts!''',
                'category': categories[3],  # Lifestyle
                'published': True,
                'featured': True,
            },
            {
                'title': 'Getting Started with Django',
                'content': '''Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design.

Here are some key features of Django:

1. **Object-Relational Mapping (ORM)**: Django provides a powerful ORM that lets you interact with your database using Python code instead of SQL.

2. **Admin Interface**: Django automatically generates an admin interface for your models.

3. **URL Routing**: Clean and elegant URL design with powerful routing capabilities.

4. **Template System**: A flexible template system with inheritance and custom tags.

5. **Security Features**: Built-in protection against common security threats.

This blog itself is built using Django and showcases many of these features!''',
                'category': categories[0],  # Technology
                'published': True,
                'featured': True,
            },
            {
                'title': 'Top 10 Travel Destinations for 2024',
                'content': '''Planning your next adventure? Here are the top 10 travel destinations you should consider for 2024:

1. **Japan** - Experience the perfect blend of traditional and modern culture
2. **Iceland** - Stunning natural landscapes and the Northern Lights
3. **New Zealand** - Adventure sports and breathtaking scenery
4. **Portugal** - Beautiful coastlines and historic cities
5. **Costa Rica** - Rich biodiversity and eco-tourism
6. **Morocco** - Exotic culture and stunning architecture
7. **Vietnam** - Delicious food and beautiful landscapes
8. **Greece** - Ancient history and beautiful islands
9. **Canada** - Vast wilderness and friendly people
10. **Australia** - Unique wildlife and diverse landscapes

Each destination offers unique experiences and memories that will last a lifetime!''',
                'category': categories[1],  # Travel
                'published': True,
                'featured': False,
            },
            {
                'title': 'Easy Homemade Pizza Recipe',
                'content': '''Nothing beats a homemade pizza! Here's a simple recipe that anyone can follow:

**Ingredients:**
- 2 cups all-purpose flour
- 1 packet active dry yeast
- 1 tsp salt
- 1 tbsp olive oil
- 3/4 cup warm water
- Pizza sauce
- Mozzarella cheese
- Your favorite toppings

**Instructions:**
1. Mix flour, yeast, and salt in a bowl
2. Add olive oil and warm water, mix until dough forms
3. Knead for 5-10 minutes until smooth
4. Let rise for 1 hour
5. Roll out dough, add sauce and toppings
6. Bake at 475°F for 12-15 minutes

Enjoy your homemade pizza!''',
                'category': categories[2],  # Food
                'published': True,
                'featured': False,
            },
            {
                'title': 'The Importance of Work-Life Balance',
                'content': '''In today's fast-paced world, maintaining a healthy work-life balance has become more important than ever.

**Why Work-Life Balance Matters:**

- **Mental Health**: Reduces stress and prevents burnout
- **Physical Health**: More time for exercise and proper rest
- **Relationships**: Quality time with family and friends
- **Productivity**: Better focus when you're well-rested
- **Personal Growth**: Time for hobbies and self-improvement

**Tips for Better Balance:**

1. Set clear boundaries between work and personal time
2. Learn to say no to non-essential commitments
3. Take regular breaks throughout the day
4. Prioritize your tasks effectively
5. Make time for activities you enjoy
6. Get enough sleep
7. Stay organized

Remember, work-life balance looks different for everyone. Find what works best for you!''',
                'category': categories[3],  # Lifestyle
                'published': True,
                'featured': False,
            },
        ]

        # Create posts
        for post_data in posts_data:
            slug = slugify(post_data['title'])
            post, created = Post.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': post_data['title'],
                    'content': post_data['content'],
                    'author': admin_user,
                    'category': post_data['category'],
                    'published': post_data['published'],
                    'featured': post_data['featured'],
                }
            )
            if created:
                self.stdout.write(f'Created post: {post.title}')

        self.stdout.write(self.style.SUCCESS('Successfully loaded sample data!'))