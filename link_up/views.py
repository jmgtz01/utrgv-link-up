from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html', {})


def about(request):
    return render(request, 'about.html', {})


def available_computers(request):
    return render(request, 'available-computers.html', {})


def study_groups(request):
    return render(request, 'study-groups.html', {})


def instant_message(request):
    return render(request, 'instant-message.html', {})


def events(request):
    return render(request, 'events.html', {})


def resources(request):
    return render(request, 'resources.html', {})
