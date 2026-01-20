# # US-14: Django Website - Basic Views
import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import LoginForm

BACKEND_URL = "http://127.0.0.1:5000"

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
                # Store token in session
                request.session["access_token"] = access_token
                request.session["username"] = username
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
    try:
        # Fetch products
        prod_res = requests.get(f"{BACKEND_URL}/api/products")
        if prod_res.status_code == 200:
            products = prod_res.json()
        
        # Fetch user's subscriptions
        sub_res = requests.get(f"{BACKEND_URL}/api/subscriptions", params={"username": username})
        if sub_res.status_code == 200:
            subscriptions = sub_res.json()
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")

    return render(request, "dashboard.html", {
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
    try:
        requests.post(f"{BACKEND_URL}/api/subscriptions", json={
            "username": username,
            "product_id": product_id
        })
    except Exception as e:
        print(f"Error subscribing: {e}")
    
    return redirect("dashboard")

