from django.contrib import admin
from django.urls import path
from Auth import views

urlpatterns = [
    path('', views.Auth, name="Auth"),
    path('logout', views.Logout, name="Logout"),

]