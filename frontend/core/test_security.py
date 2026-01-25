from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings

class SecurityAcceptanceTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client(enforce_csrf_checks=True)

    def test_csrf_protection_enabled(self):
        """
        DoD: Django's built-in security middleware is enabled.
        AC: Given enabled middleware, when CSRF attempted, then blocked.
        """
        # Ensure middleware is actually in settings
        middleware = settings.MIDDLEWARE
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', middleware)

        # Attempt a POST request without a CSRF token
        # We target a login endpoint or any POST endpoint
        # Using a generic path that likely requires POST, e.g., login
        response = self.client.post('/login/', {'login': 'testuser', 'password': 'password123'})
        
        # Without CSRF token, it should be 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Verify that with a client that handles CSRF properly (like the test client usually does by default, 
        # but we enforced checks), we can get a token or the view works if we follow proper flow.
        # Standard test client handles CSRF automatically unless enforced otherwise manually.
        # But 'enforce_csrf_checks=True' on Client() means we MUST send it if we construct requests manually.
        
        # Let's verify we CAN succeed if we do it "right" (simulating a browser flow is harder in unit tests 
        # without fetching the token first, but the 403 confirms the protection is ACTIVE).

    def test_orm_prevents_sql_injection(self):
        """
        AC: Given malicious query, when executed, then prevented by ORM.
        """
        # Attempt to inject SQL via username. 
        # We try to find a user with a payload that would verify injection if it worked.
        # Payload: "admin' OR '1'='1"
        malicious_input = "admin' OR '1'='1"
        
        # If injection works, this filter might return all users or the admin user.
        # If safe, it searches for a user with literally that name.
        users = User.objects.filter(username=malicious_input)
        
        # We expect 0 results because no user has that weird name.
        self.assertEqual(users.count(), 0)
        
        # Double check: Create a user with that literal name to prove it's treated literally
        User.objects.create_user(username=malicious_input, password='pw')
        users_safe = User.objects.filter(username=malicious_input)
        self.assertEqual(users_safe.count(), 1)
        self.assertEqual(users_safe.first().username, malicious_input)
