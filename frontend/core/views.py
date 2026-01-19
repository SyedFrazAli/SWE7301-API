# # US-14: Django Website - Basic Views
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm


def index(request):
    """Simple view to test Django is running"""
    return JsonResponse({
        'status': 'success',
        'message': 'Django is running!',
        'project': 'GeoScope Analytics - US-14'
    })


def home(request):
    """Serve the static HTML page"""
    return render(request, 'index.html')


def login_view(request):
    form = LoginForm(request.POST or None)
    error = None

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")  # change to your home URL
        else:
            error = "Invalid username or password"

    return render(request, "login.html", {"form": form, "error": error})

