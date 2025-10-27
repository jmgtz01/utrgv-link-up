from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('about', views.about, name="about"),
    path('available-computers', views.available_computers, name="available-computers"),
    path('study-groups', views.study_groups, name="study-groups"),
    path('instant-message', views.instant_message, name="instant-message"),
    path('events', views.events, name="events"),
    path('resources', views.resources, name="resources"),
]
