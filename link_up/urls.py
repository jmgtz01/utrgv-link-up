from django.urls import path
from . import views

app_name = "link_up"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("available_computers/", views.available_computers,
         name="available_computers"),
    path("study-groups/", views.study_groups, name="study_groups"),
    path("instant-message/", views.instant_message, name="instant_message"),
    path("events/", views.events, name="events"),
    path("resources/", views.resources, name="resources"),
    path("api/status/", views.update_status, name="update_status"),
    path("api/position/", views.update_position, name="update_position"),
    path("api/slots/", views.available_slots, name="available_slots"),
    path("api/reserve/", views.create_reservation, name="create_reservation"),
    path("api/cancel-reservation/", views.cancel_reservation, name="cancel_reservation"),
    path("add-venue/", views.add_venue, name="add-venue"),
    path('list_venues', views.list_venues, name='list-venues'),
    path('show_venue/<venue_id>', views.show_venue, name='show-venue'),
    path('update_venue/<venue_id>', views.update_venue, name="update-venue"),
    path("add-events/", views.add_events, name="add-events"),
    path('update_event/<event_id>', views.update_event, name="update-event"),
    path('delete_event/<event_id>', views.delete_event, name="delete-event"),
    path('delete_venue/<venue_id>', views.delete_venue, name="delete-venue"),
    path('attend/<int:event_id>/', views.attend_event, name='attend-event'),
    path('not-attend/<int:event_id>', views.not_attend, name="not-attend"),
    path('my-events/', views.my_events, name='my-events'),
    path('all-events-student/', views.all_events_student,
         name='all-events-student'),
]
