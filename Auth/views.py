from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

def Auth(request):
    login_form = AuthenticationForm()
    signup_form = UserCreationForm()
    if request.method == 'POST':
        if 'login-form' in request.POST:
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                username = login_form.cleaned_data.get('username')
                password = login_form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect(request.GET.get('next', 'home'))
        elif 'signup-form' in request.POST:
            signup_form = UserCreationForm(request.POST)
            if signup_form.is_valid():
                user = signup_form.save()
                login(request, user)
                return redirect(request.GET.get('next', 'home'))
        
    return render(request, "Auth/index.html", {'login_form': login_form, 'signup_form': signup_form, "login_errors": login_form.errors, "signup_errors": signup_form.errors})

def Logout(request):
    logout(request)
    return redirect("Auth")
