# # US-14: Django Website - Basic Views
import requests
import os
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import LoginForm

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")

def index(request):
    """Landing page view"""
    return render(request, 'index.html')


def home(request):
    """Serve the static HTML page"""
    return render(request, 'index.html')


def login_view(request):
    form = LoginForm(request.POST or None)
    error = None

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        
        try:
            response = requests.post(f"{BACKEND_URL}/login", json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token")
                user_info = data.get("user", {})
                
                # Store tokens and user info in session
                request.session["access_token"] = access_token
                request.session["refresh_token"] = refresh_token
                request.session["username"] = username
                request.session["user_info"] = user_info
                return redirect("dashboard")
            else:
                error = "Invalid username or password"
        except requests.exceptions.RequestException as e:
            error = f"Backend connection error: {str(e)}"

    return render(request, "login.html", {"form": form, "error": error})


def signup_view(request):
    """Handle user signup"""
    error = None

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        try:
            response = requests.post(f"{BACKEND_URL}/signup", json={
                "username": request.POST.get("username"),
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password
            })
            
            if response.status_code == 200 or response.status_code == 201:
                # Redirect to login after successful signup
                return redirect("login")
            else:
                error = response.json().get("message", "Signup failed")
        except requests.exceptions.RequestException as e:
            error = f"Backend connection error: {str(e)}"

    return render(request, "signup.html", {"error": error})


def dashboard(request):
    """Dashboard view protected by session token"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    username = request.session.get("username", "User")
    
    products = []
    subscriptions = []
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Fetch products
        prod_res = requests.get(f"{BACKEND_URL}/api/products", headers=headers)
        if prod_res.status_code == 200:
            products = prod_res.json()
        
        # Fetch user's subscriptions (backend expects user_id query parameter)
        sub_res = requests.get(f"{BACKEND_URL}/api/subscriptions", params={"user_id": username}, headers=headers)
        if sub_res.status_code == 200:
            subscriptions = sub_res.json()
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")

    return render(request, "dashboard.html", {
        "username": username,
        "products": products,
        "subscriptions": subscriptions,
        "backend_connected": True if (products or subscriptions) else False,
        "access_token": access_token,
        "refresh_token": request.session.get("refresh_token"),
        "backend_url": BACKEND_URL
    })


def subscriptions(request):
    """Subscriptions view protected by session token"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    username = request.session.get("username", "User")
    
    products = []
    subscriptions = []
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Fetch products
        prod_res = requests.get(f"{BACKEND_URL}/api/products", headers=headers)
        if prod_res.status_code == 200:
            products = prod_res.json()
        
        # Fetch user's subscriptions (backend expects user_id query parameter)
        sub_res = requests.get(f"{BACKEND_URL}/api/subscriptions", params={"user_id": username}, headers=headers)
        if sub_res.status_code == 200:
            subscriptions = sub_res.json()
    except Exception as e:
        print(f"Error fetching subscription data: {e}")

    return render(request, "subscriptions.html", {
        "username": username,
        "products": products,
        "subscriptions": subscriptions
    })


def subscribe(request, product_id):
    """Handle product subscription"""
    access_token = request.session.get("access_token")
    if not access_token:
        return redirect("login")
    
    username = request.session.get("username")
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        requests.post(f"{BACKEND_URL}/api/subscriptions", json={
            "user_id": username,
            "product_id": product_id
        }, headers=headers)
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

