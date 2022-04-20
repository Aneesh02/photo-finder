from django.urls import path, include
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('home', views.home, name='home'),
    path('accounts/', include('allauth.urls')),
    path("delete/", views.deletePhoto, name="delete"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path("process", views.process, name="process"),
]