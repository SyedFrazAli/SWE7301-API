# US-14: Django Website - Basic URLs
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('dashboard/update-token/', views.update_token_view, name='update_token'),
    path('observations/', views.observations, name='observations'),
    path('satellites/', views.satellites, name='satellites'),
    path('subscribe/<int:product_id>/', views.subscribe, name='subscribe'),
    path('verify-2fa-endpoint/', views.verify_2fa_view, name='verify_2fa_endpoint'),
    path('google-login-endpoint/', views.google_login_view, name='google_login_endpoint'),
    path('auth/google/callback', views.google_callback_view, name='google_callback'),
    path('setup-2fa/', views.setup_2fa_view, name='setup_2fa'),
    path('verify-2fa-setup/', views.verify_2fa_setup_view, name='verify_2fa_setup'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('verify-login-otp/', views.verify_login_otp_view, name='verify_login_otp'),
    path('settings/', views.settings, name='settings'),
    path('setup-2fa-endpoint/', views.setup_2fa_json_view, name='setup_2fa_endpoint'),
    path('disable-2fa/', views.disable_2fa_view, name='disable_2fa'),
    path('update-profile/', views.update_profile_view, name='update_profile'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
]
