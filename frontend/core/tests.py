from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
import requests

class ViewTests(TestCase):
    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    @patch('requests.post')
    def test_login_view_success(self, mock_post):
        # Mock successful backend response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "fake-jwt-token"}
        
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'password'
        })
        
        # Check for redirect to dashboard
        self.assertRedirects(response, reverse('dashboard'))
        # Check if token is in session
        self.assertEqual(self.client.session['access_token'], 'fake-jwt-token')
        self.assertEqual(self.client.session['username'], 'admin')

    def test_dashboard_access_denied_if_not_logged_in(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('login'))

    def test_dashboard_access_allowed_if_logged_in(self):
        session = self.client.session
        session['access_token'] = 'fake-jwt-token'
        session['username'] = 'testuser'
        session.save()
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back, testuser")

    def test_dashboard_contains_token_manager(self):
        # When a user has tokens in session, the dashboard should show token manager UI
        session = self.client.session
        session['access_token'] = 'fake-jwt-token'
        session['refresh_token'] = 'fake-refresh'
        session['username'] = 'admin'
        session.save()

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "JWT Token Management")
        self.assertContains(response, 'id="accessToken"')
        self.assertContains(response, 'id="refreshToken"')

    def test_dashboard_includes_dashboard_css(self):
        session = self.client.session
        session['access_token'] = 'fake-jwt-token'
        session['username'] = 'admin'
        session.save()

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dashboard.css')

    @patch('requests.post')
    def test_subscribe_posts_user_id(self, mock_post):
        session = self.client.session
        session['access_token'] = 'fake-jwt-token'
        session['username'] = 'user123'
        session.save()

        response = self.client.get(reverse('subscribe', args=[5]))
        # subscribe view redirects back to dashboard
        self.assertEqual(response.status_code, 302)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/api/subscriptions', args[0])
        self.assertEqual(kwargs['json']['user_id'], 'user123')
        self.assertEqual(kwargs['json']['product_id'], 5)

    @patch('requests.post')
    def test_login_view_failure(self, mock_post):
        # Mock failed backend response
        mock_post.return_value.status_code = 401
        
        response = self.client.post(reverse('login'), {
            'username': 'wrong',
            'password': 'wrong'
        })
        
        # Should stay on login page and show error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")
        self.assertNotIn('access_token', self.client.session)

    @patch('requests.post')
    def test_signup_posts_username(self, mock_post):
        mock_post.return_value.status_code = 201
        response = self.client.post(reverse('signup'), {
            'first_name': 'Test',
            'username': 'testuser',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'password'
        })
        # on success, signup view redirects to login
        self.assertEqual(response.status_code, 302)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/signup', args[0])
        self.assertEqual(kwargs['json']['username'], 'testuser')
