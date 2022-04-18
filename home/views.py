from django.shortcuts import render, redirect
from django.contrib.auth.models import User

# Create your views here.
def login(request):
    user = request.user
    if user.is_anonymous:
        return render(request, 'login.html')
    else:
        return redirect('/home')

def home(request):
    user = request.user
    if user.is_anonymous:
        return redirect('/')
    else:
        return render(request, 'home.html')