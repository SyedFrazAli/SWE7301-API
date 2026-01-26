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


def observations(request):
    """Observations view protected by session token"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    username = request.session.get("username", "User")
    observations_data = []
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Fetching observations from your backend API
        response = requests.get(f"{BACKEND_URL}/api/observations", params={"username": username}, headers=headers)
        if response.status_code == 200:
            observations_data = response.json()
    except Exception as e:
        print(f"Error fetching observations: {e}")

    return render(request, "observations.html", {
        "username": username,
        "observations": observations_data
    })

def satellites(request):
    """View to display satellite constellation status"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    username = request.session.get("username", "User")
    
    # Example data structure - replace with API call later
    satellite_list = [
        {"name": "Sentinel-2A", "status": "Active", "sensor": "MSI", "orbit": "Sun-synchronous", "last_seen": "12 mins ago"},
        {"name": "Sentinel-2B", "status": "Active", "sensor": "MSI", "orbit": "Sun-synchronous", "last_seen": "45 mins ago"},
        {"name": "Landsat-8", "status": "Maintenance", "sensor": "OLI/TIRS", "orbit": "Near-polar", "last_seen": "2 hours ago"},
        {"name": "GeoScope-P1", "status": "Active", "sensor": "SAR", "orbit": "Low Earth", "last_seen": "Just now"},
    ]

    return render(request, "satellites.html", {
        "username": username,
        "satellites": satellite_list
    })


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
        # Determine Plan Name
        plan_name = "Free Plan"
        if subscriptions:
             # Check for Pro Plan (ID 5)
             has_pro = any(s.get('product_id') == 5 for s in subscriptions)
             if has_pro:
                 plan_name = "Pro Plan"
             else:
                 plan_name = "Standard Plan"

    except requests.exceptions.RequestException as e:
        print(f"Error fetching dashboard data (request error): {e}")
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")

    return render(request, "dashboard.html", {
        "username": username,
        "plan_name": plan_name,
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
    # Display name logic
    display_name = request.session.get("first_name") or user_email.split('@')[0].capitalize()
    
    products = []
    subscriptions = []
    pro_plan = None
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        
        prod_res = requests.get(f"{BACKEND_URL}/api/products", headers=headers, timeout=REQUEST_TIMEOUT)
        if prod_res.status_code == 200:
            all_products = prod_res.json()
            
            
            product_map = {p['id']: p for p in all_products}

           
            products = [p for p in all_products if p['id'] != 9]
            pro_plan = next((p for p in all_products if p['id'] == 9), None)
        else:
            all_products = []
            product_map = {}
        
      
        sub_res = requests.get(f"{BACKEND_URL}/api/subscriptions", params={"user_id": user_email}, headers=headers, timeout=REQUEST_TIMEOUT)
        if sub_res.status_code == 200:
            raw_subs = sub_res.json()
            
           
            for sub in raw_subs:
                p_id = sub.get('product_id')
                
                sub['product'] = product_map.get(p_id, {
                    "name": f"Product #{p_id}", 
                    "description": "Details unavailable", 
                    "price": "N/A"
                })
            subscriptions = raw_subs

    except requests.exceptions.RequestException as e:
        print(f"Error fetching subscription data: {e}")
        
    return render(request, "subscriptions.html", {
        "username": display_name,
        "products": products,
        "pro_plan": pro_plan,
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
        # POST to backend to get Checkout Session URL
        response = requests.post(f"{BACKEND_URL}/api/create-checkout-session", json={
            "user_email": user_email,
            "product_id": product_id
        }, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
             data = response.json()
             if data.get("checkout_url"):
                 return redirect(data.get("checkout_url"))
             else:
                 print("No checkout URL returned")
        else:
            print(f"Error creating checkout session: {response.text}")
            
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
    return render(request, "payment_success.html", {"BACKEND_URL": BACKEND_URL})


def payment_failed(request):
    """Render payment failed page"""
    return render(request, "payment_failed.html")