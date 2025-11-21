from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from .forms import RegisterUserForm
import json

def login_user(request):
    is_json = request.content_type == "application/json" or request.headers.get(
        "X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        if is_json:
            try:
                data = json.loads(request.body.decode())
                username = data.get("username", "")
                password = data.get("password", "")
            except Exception:
                return JsonResponse({"ok": False, "error": "Bad payload"}, status=400)
        else:
            username = request.POST.get("username", "")
            password = request.POST.get("password", "")
        next_url = request.POST.get("next") or request.GET.get("next")
        if not next_url:
            next_url = request.META.get("HTTP_REFERER")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if is_json:
                return JsonResponse({"ok": True})
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('link_up:home')
        else:
            if is_json:
                return JsonResponse({"ok": False, "error": "Invalid username or password"}, status=400)
            messages.success(request, ("Invalid username or password. Please try again."))
            return render(request, 'authenticate/login.html', {})
    else:
        return render(request, 'authenticate/login.html', {})
    
def logout_user(request):
    logout(request)
    messages.success(request, ("You were logged out."))
    return redirect('link_up:home')

def register_user(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("Registration Successful"))
            return redirect('link_up:home')
    else:
        form = RegisterUserForm()
    return render(request, 'authenticate/register_user.html', {
        'form': form,
    })
