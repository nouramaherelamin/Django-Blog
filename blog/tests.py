from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Post, Comment

class BlogTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(name='Technology')
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='This is a test content.',
            author=self.user,
            category=self.category,
            published=True
        )

    def test_home_view(self):
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_post_detail_view(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertContains(response, 'This is a test content.')

    def test_category_view(self):
        response = self.client.get(reverse('blog:category_posts', args=[self.category.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Technology')

    def test_author_view(self):
        response = self.client.get(reverse('blog:author_posts', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_search_functionality(self):
        response = self.client.get(reverse('blog:home'), {'search': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_comment_submission(self):
        response = self.client.post(self.post.get_absolute_url(), {
            'name': 'John Doe',
            'email': 'john@example.com',
            'content': 'Great post!'
        })
        self.assertEqual(response.status_code, 302)  # Redirects on success
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().name, 'John Doe')

    def test_like_post_ajax(self):
        response = self.client.post(
            reverse('blog:like_post', args=[self.post.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
