# # US-14: Django Website - Basic Views
import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import LoginForm

# Use settings-based backend URL so it's configurable per-environment
BACKEND_URL = getattr(settings, "BACKEND_API_URL", "http://127.0.0.1:5000")
REQUEST_TIMEOUT = 5  # seconds

def index(request):
    """Landing page view"""
    return render(request, 'index.html')


def home(request):
    """Serve the static HTML page"""
    return render(request, 'index.html')


def login_view(request):
    """Handle user login"""
    error = None

    if request.method == "POST":
        try:
            # Handle AJAX JSON request
            if request.content_type == 'application/json':
                import json
                data = json.loads(request.body)
            else:
                form = LoginForm(request.POST) # Not used, just use raw post
                data = {
                    "email": request.POST.get("email"),
                    "password": request.POST.get("password")
                }

            response = requests.post(f"{BACKEND_URL}/login", json=data, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                res_data = response.json()
                
                # Check for various 2FA requirements
                if res_data.get("otp_required") or res_data.get("two_step_required"):
                     # Just return the JSON so frontend can handle switching to OTP view
                     return JsonResponse(res_data)
                
                # Success - Normal login
                request.session["access_token"] = res_data.get("access_token")
                request.session["refresh_token"] = res_data.get("refresh_token")
                user = res_data.get("user", {})
                request.session["username"] = user.get("email")
                request.session["first_name"] = user.get("first_name", "User")
                
                if request.content_type == 'application/json':
                    return JsonResponse({"success": True, "redirect_url": "/dashboard/"})
                return redirect("dashboard")
            else:
                msg = response.json().get("msg", "Invalid email or password")
                if request.content_type == 'application/json':
                    return JsonResponse({"error": msg}, status=response.status_code)
                error = msg
        except requests.exceptions.RequestException as e:
            if request.content_type == 'application/json':
                return JsonResponse({"error": f"Backend connection error: {str(e)}"}, status=500)
            error = f"Backend connected error"

    return render(request, "login.html", {"error": error})

def verify_login_otp_view(request):
    """Handle login OTP verification"""
    if request.method == "POST":
        try:
            import json
            data = json.loads(request.body)
            
            response = requests.post(f"{BACKEND_URL}/verify-login-otp", json=data, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                res_data = response.json()
                
                if res_data.get("totp_required"):
                    # Authenticator App Check Required
                    return JsonResponse(res_data)
                
                # Success
                request.session["access_token"] = res_data.get("access_token")
                request.session["refresh_token"] = res_data.get("refresh_token")
                user = res_data.get("user", {})
                request.session["username"] = user.get("email")
                request.session["first_name"] = user.get("first_name", "User")
                
                return JsonResponse({"success": True, "redirect_url": "/dashboard/"})
            else:
                return JsonResponse(response.json(), status=response.status_code)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def verify_2fa_view(request):
    """AJAX view to verify 2FA code"""
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        email = data.get("email") or data.get("username")
        otp_code = data.get("otp_code")
        
        try:
            response = requests.post(f"{BACKEND_URL}/2fa/verify", json={
                "email": email,
                "otp_code": otp_code
            }, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                res_data = response.json()
                request.session["access_token"] = res_data.get("access_token")
                request.session["refresh_token"] = res_data.get("refresh_token")
                request.session["username"] = email
                request.session["user_info"] = res_data.get("user")
                return JsonResponse({"success": True, "redirect_url": "/dashboard/"})
            else:
                return JsonResponse({"success": False, "error": "Invalid OTP code"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"status": "error"}, status=405)


def google_login_view(request):
    """
    Redirects to Backend Google Login to start OAuth flow.
    """
    return redirect(f"{BACKEND_URL}/google-login")


def google_callback_view(request):
    """
    Handles callback from Backend after successful Google OAuth.
    Captures tokens from URL parameters and sets session.
    """
    access_token = request.GET.get("access_token")
    refresh_token = request.GET.get("refresh_token")
    email = request.GET.get("email")

    if access_token and refresh_token:
        request.session["access_token"] = access_token
        request.session["refresh_token"] = refresh_token
        request.session["username"] = email 
        request.session["first_name"] = request.GET.get("first_name", "User")
        
        is_2fa = request.GET.get("is_2fa_enabled")
        # Direct redirect to dashboard, skipping mandatory 2FA setup
        return redirect("dashboard")
    else:
        return render(request, "login.html", {"error": "Google Login Failed: Missing tokens."})

def setup_2fa_view(request):
    """Render 2FA setup page"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    return render(request, "setup_2fa.html", {
        "backend_url": BACKEND_URL,
        "access_token": access_token
    })

def verify_2fa_setup_view(request):
    """AJAX handler for creating 2FA setup"""
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        otp_code = data.get("otp_code")
        email = request.session.get("username")
        
        try:
            response = requests.post(f"{BACKEND_URL}/2fa/verify", json={
                "email": email,
                "otp_code": otp_code,
                "setup_mode": True
            }, headers={'Authorization': f'Bearer {access_token}'}, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                res_data = response.json()
                # Update tokens if refreshed
                request.session["access_token"] = res_data.get("access_token", request.session.get("access_token"))
                return JsonResponse({"success": True, "redirect_url": "/dashboard/"})
            else:
                return JsonResponse({"success": False, "error": "Invalid OTP Code"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"status": "error"}, 405)


def signup_view(request):
    """Handle user signup"""
    error = None

    if request.method == "POST":
        try:
            # Handle AJAX JSON request
            if request.content_type == 'application/json':
                import json
                data = json.loads(request.body)
            else:
                # Handle Form Data
                data = {
                    "first_name": request.POST.get("first_name"),
                    "last_name": request.POST.get("last_name"),
                    "email": request.POST.get("email"),
                    "password": request.POST.get("password")
                }

            response = requests.post(f"{BACKEND_URL}/signup", json=data, timeout=REQUEST_TIMEOUT)
            
            if response.status_code in [200, 201]:
                return JsonResponse(response.json())
            else:
                return JsonResponse(response.json(), status=response.status_code)
                
        except requests.exceptions.RequestException as e:
            if request.content_type == 'application/json':
               return JsonResponse({"error": f"Backend connection error: {str(e)}"}, status=500)
            error = f"Backend connection error: {str(e)}"

    return render(request, "signup.html", {"error": error})

def verify_email_view(request):
    """Handle email verification"""
    if request.method == "POST":
        try:
            import json
            data = json.loads(request.body)
            
            response = requests.post(f"{BACKEND_URL}/verify-email", json=data, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                res_data = response.json()
                # Set session
                request.session["access_token"] = res_data.get("access_token")
                request.session["refresh_token"] = res_data.get("refresh_token")
                user = res_data.get("user", {})
                request.session["username"] = user.get("email")
                request.session["first_name"] = user.get("first_name", "User")
                
                return JsonResponse({"success": True, "redirect_url": "/dashboard/"})
            else:
                return JsonResponse(response.json(), status=response.status_code)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def dashboard(request):
    """Dashboard view protected by session token"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    # username for display (first_name preferred), user_email for backend queries
    username = request.session.get("first_name") or request.session.get("username", "User")
    user_email = request.session.get("username") or request.session.get("user_email")
    
    products = []
    subscriptions = []
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Fetch products
        prod_res = requests.get(f"{BACKEND_URL}/api/products", headers=headers, timeout=REQUEST_TIMEOUT)
        if prod_res.status_code == 200:
            products = prod_res.json()
        
        # Fetch user's subscriptions (backend expects user_id)
        if user_email:
            sub_res = requests.get(f"{BACKEND_URL}/api/subscriptions", params={"user_id": user_email}, headers=headers, timeout=REQUEST_TIMEOUT)
            if sub_res.status_code == 200:
                subscriptions = sub_res.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching dashboard data (request error): {e}")
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")

    return render(request, "dashboard.html", {
        "username": username,
        "products": products,
        "subscriptions": subscriptions,
        "backend_connected": prod_res.status_code == 200 if 'prod_res' in locals() else False
    })


def subscriptions(request):
    """Subscriptions view protected by session token"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    user_email = request.session.get("username") or request.session.get("user_email") or "User"
    display_name = user_email.split('@')[0].capitalize() if user_email != "User" else "User"
    
    products = []
    subscriptions = []
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Fetch products
        prod_res = requests.get(f"{BACKEND_URL}/api/products", headers=headers, timeout=REQUEST_TIMEOUT)
        if prod_res.status_code == 200:
            products = prod_res.json()
        
        # Fetch user's subscriptions (backend expects user_id)
        sub_res = requests.get(f"{BACKEND_URL}/api/subscriptions", params={"user_id": user_email}, headers=headers, timeout=REQUEST_TIMEOUT)
        if sub_res.status_code == 200:
            subscriptions = sub_res.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching subscription data (request error): {e}")
    except Exception as e:
        print(f"Error fetching subscription data: {e}")

    return render(request, "subscriptions.html", {
        "username": display_name,
        "products": products,
        "subscriptions": subscriptions
    })


def subscribe(request, product_id):
    """Handle product subscription"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    user_email = request.session.get("username") or request.session.get("user_email")
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        requests.post(f"{BACKEND_URL}/api/subscriptions", json={
            "user_id": user_email,
            "product_id": product_id
        }, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        print(f"Error subscribing (request error): {e}")
    except Exception as e:
        print(f"Error subscribing: {e}")
    
    return redirect("dashboard")


def update_token_view(request):
    """Update access token in session - US-16 requirement"""
    if request.method == "POST":
        try:
            import json
            data = json.loads(request.body)
            access_token = data.get("access_token")
            
            if access_token:
                request.session["access_token"] = access_token
                return JsonResponse({"status": "success", "message": "Token updated"})
            else:
                return JsonResponse({"status": "error", "message": "No token provided"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)


def settings(request):
    """Settings page"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        # Validate token and get fresh user info
        response = requests.post(f"{BACKEND_URL}/token/validate", headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            user_info = response.json().get("user")
            return render(request, "settings.html", {"user_info": user_info})
    except:
        pass
    return redirect("login")

def setup_2fa_json_view(request):
    """Get QR code for 2FA setup (JSON)"""
    access_token = request.session.get("access_token")
    if not access_token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.post(f"{BACKEND_URL}/2fa/setup", headers=headers, timeout=REQUEST_TIMEOUT)
        return JsonResponse(response.json(), status=response.status_code)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def disable_2fa_view(request):
    """Disable 2FA"""
    access_token = request.session.get("access_token")
    if not access_token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
        
    # Standard POST check
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.post(f"{BACKEND_URL}/2fa/disable", headers=headers, timeout=REQUEST_TIMEOUT)
        return JsonResponse(response.json(), status=response.status_code)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def update_profile_view(request):
    """Handle profile update"""
    access_token = request.session.get("access_token")
    if not access_token:
        return JsonResponse({"error": "Unauthorized"}, status=401)
        
    if request.method == "POST":
        try:
            import json
            data = json.loads(request.body)
            
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.put(f"{BACKEND_URL}/api/profile", json=data, headers=headers, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                # Update session
                res_data = response.json()
                user = res_data.get("user", {})
                request.session["first_name"] = user.get("first_name")
                request.session["username"] = user.get("email")
                return JsonResponse({"success": True})
            else:
                return JsonResponse(response.json(), status=response.status_code)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)

def payment_success(request):
    """Render payment success page"""
    return render(request, "payment_success.html")


def payment_failed(request):
    """Render payment failed page"""
    return render(request, "payment_failed.html")