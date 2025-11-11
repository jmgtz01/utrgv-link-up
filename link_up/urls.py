from django.urls import path
from . import views

app_name = "link_up"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("available_computers/", views.available_computers, name="available_computers"),
    path("study-groups/", views.study_groups, name="study_groups"),
    path("instant-message/", views.instant_message, name="instant_message"),
    path("events/", views.events, name="events"),
    path("resources/", views.resources, name="resources"),

    path("api/position/", views.update_position, name="update_position"),
]
