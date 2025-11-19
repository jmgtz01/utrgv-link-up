from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import Computer, StudyRoom
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
import json
from .models import Computer, StudyRoom
from .models import COMPUTER_STATUSES, ROOM_STATUSES
from django.contrib.auth.decorators import login_required
import calendar
from calendar import HTMLCalendar
from datetime import datetime
from .models import Event, Venue
from .forms import VenueForm, EventForm
from django.http import HttpResponseRedirect
from django.urls import reverse


@login_required
@require_POST
def update_position(request):
    try:
        data = json.loads(request.body.decode())
        item_type = data["type"]      # "computer" or "room"
        pk = int(data["id"])
        x = float(data["x"])
        y = float(data["y"])
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    obj = (Computer if item_type ==
           "computer" else StudyRoom).objects.filter(pk=pk).first()
    if not obj:
        return HttpResponseBadRequest("Not found")

    obj.x, obj.y = x, y
    obj.save(update_fields=["x", "y"])
    return JsonResponse({"ok": True})


@login_required
@require_POST
def update_status(request):
    try:
        data = json.loads(request.body.decode())
        item_type = data["type"]
        pk = int(data["id"])
        new_status = data["status"]  # This is the *desired* new status
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    Model = (Computer if item_type == "computer" else StudyRoom)
    obj = Model.objects.filter(pk=pk).first()
    if not obj:
        return HttpResponseBadRequest("Not found")

    # --- ADMIN LOGIC ---
    if request.user.is_staff:
        # Admins can do anything
        obj.status = new_status
        if new_status == "reserved":
            obj.reserved_by = request.user  # Admin reserves for themself
        else:
            obj.reserved_by = None  # Any other status clears reservation
        obj.save()
        return JsonResponse({"ok": True})

    # --- REGULAR USER LOGIC ---
    # Case 1: User is reserving an "available" computer
    if obj.status == "available" and new_status == "reserved":
        obj.status = "reserved"
        obj.reserved_by = request.user
        obj.save(update_fields=["status", "reserved_by"])
        return JsonResponse({"ok": True})

    # Case 2: User is un-reserving *their own* computer
    if obj.status == "reserved" and obj.reserved_by == request.user and new_status == "available":
        obj.status = "available"
        obj.reserved_by = None
        obj.save(update_fields=["status", "reserved_by"])
        return JsonResponse({"ok": True})

    # Case 3: Any other action is forbidden for a regular user
    return HttpResponseBadRequest("Action not allowed")


def home(request):
    return render(request, 'home.html', {})


def about(request):
    return render(request, 'about.html', {})


def available_computers(request):
    icon_map = {
        "computer": {
            "available": "img/available.png",
            "reserved":  "img/reserved.png",
            "occupied":  "img/lock.png",
            "repair":    "img/bsod.png",
        },
        "room": {
            "available":    "img/sravailable.png",
            "reserved":     "img/srreserved.png",
            "occupied":     "img/sroccupied.png",
            "out_of_order": "img/sroutoforder.png",
        },
    }

    # Precompute icon path for each item
    computers = []
    for c in Computer.objects.order_by("name"):
        d = model_to_dict(c, fields=["id", "name", "x", "y", "status"])
        is_mine = (c.reserved_by and c.reserved_by_id ==
                   request.user.id)  # Use .id for efficiency

        # --- NEW LOGIC ---
        if c.status == "reserved":
            if is_mine:
                # It's my reservation, show green check
                d["icon"] = icon_map["computer"]["available"]
                d["status"] = "reserved"  # JS needs to know it's "reserved"
            else:
                # Someone else's reservation, show lock
                d["icon"] = icon_map["computer"]["occupied"]
                d["status"] = "occupied"  # Treat it as occupied for the user
        else:
            # It's available, repair, or occupied (by non-reservation)
            d["icon"] = icon_map["computer"][c.status]
        # --- END NEW LOGIC ---

        d["is_mine"] = is_mine  # Send this to JavaScript
        computers.append(d)

    rooms = []
    for r in StudyRoom.objects.order_by("name"):
        d = model_to_dict(r, fields=["id", "name", "x", "y", "status"])
        is_mine = (r.reserved_by and r.reserved_by_id == request.user.id)

        # --- REPEAT NEW LOGIC FOR ROOMS ---
        if r.status == "reserved":
            if is_mine:
                d["icon"] = icon_map["room"]["available"]
                d["status"] = "reserved"
            else:
                d["icon"] = icon_map["room"]["occupied"]
                d["status"] = "occupied"
        else:
            d["icon"] = icon_map["room"][r.status]
        # --- END NEW LOGIC ---

        d["is_mine"] = is_mine
        rooms.append(d)

    return render(request, "available-computers.html", {
        "computers": computers,
        "rooms": rooms,
        "map_img": "img/secondfloor.png",
        "is_admin": request.user.is_staff,
        "is_authenticated": request.user.is_authenticated  # <-- THIS LINE IS NEW
    })


def study_groups(request):
    return render(request, 'study-groups.html', {})


def instant_message(request):
    return render(request, 'instant-message.html', {})


def events(request, year=datetime.now().year, month=datetime.now().strftime('%B')):
    event_list = Event.objects.none()
    if request.user.is_authenticated:
        # Check if the user is linked to a Manager profile
        if hasattr(request.user, 'manager'):
            # Manager: Filter for events where the current user is the manager
            # (Assumes the FK field in Event is named 'manager')
            event_list = Event.objects.filter(
                manager=request.user).order_by('event_date')

        # Check if the user is linked to a Student profile
        elif hasattr(request.user, 'student'):
            # Student: Filter for events where the current user's Student profile
            # is in the 'attendees' ManyToMany field
            current_student_profile = request.user.student
            event_list = Event.objects.filter(
                attendees=current_student_profile).order_by('event_date')
    name = "John"
    month = month.capitalize()
    # Covert mont from name to number
    month_number = list(calendar.month_name).index(month)
    month_number = int(month_number)

    # Create a calendar
    cal = HTMLCalendar().formatmonth(year, month_number)

    # Get current year
    now = datetime.now()
    current_year = now.year

    # Get current time
    time = now.strftime('%I:%M %p')
    return render(request, 'events.html', {
        "name": name,
        "year": year,
        "month": month,
        "month_number": month_number,
        "cal": cal,
        "current_year": current_year,
        "time": time,
        "event_list": event_list,
    })


def resources(request):
    return render(request, 'resources.html', {})


def add_venue(request):
    submitted = False
    if request.method == "POST":
        form = VenueForm(request.POST)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.owner = request.user
            venue.save()
            submitted = True
            return HttpResponseRedirect(reverse('link_up:add-venue') + '?submitted=True')
    else:
        form = VenueForm
        if 'submitted' in request.GET:
            submitted = True
    return render(request, 'add-venue.html', {
        'form': form,
        'submitted': submitted,
    })

def list_venues(request):
    if request.user.is_authenticated:
        # Filter: Only show venues owned by the current user
        venue_list = Venue.objects.filter(owner=request.user).order_by('name')
    else:
        # If the user is not logged in, show an empty list or redirect
        venue_list = []
    return render(request, 'venue.html', {
        'venue_list': venue_list,
    })

def show_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    return render(request, 'show_venue.html', {
        'venue': venue,
    })

def update_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    form = VenueForm(request.POST or None, instance=venue)
    if form.is_valid():
        form.save()
        return redirect('link_up:list-venues')
    return render(request, 'update_venue.html', {
        'venue': venue,
        'form': form,
    })


def add_events(request):
    submitted = False
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('link_up:add-events') + '?submitted=True')
    else:
        form = EventForm()
        if 'submitted' in request.GET:
            submitted = True
    return render(request, 'add-events.html', {
        'form': form,
        'submitted': submitted,
    })


def update_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    form = EventForm(request.POST or None, instance=event)
    if form.is_valid():
        form.save()
        return redirect('link_up:events')
    return render(request, 'update_event.html', {
        'event': event,
        'form': form,
    })

def delete_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    event.delete()
    return redirect('link_up:events')


def delete_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    venue.delete()
    return redirect('link_up:list-venues')


@login_required
def not_attend(request, event_id):
    # 1. Get the event or return a 404 error if it doesn't exist
    event = get_object_or_404(Event, pk=event_id)

    # 2. Check if the logged-in user has a student profile
    if hasattr(request.user, 'student'):
        current_student = request.user.student

        # 3. Remove the student profile from the event's attendees list
        # The remove() method on the M2M manager handles the deletion.
        event.attendees.remove(current_student)

    # 4. Redirect the user back to the events list page
    return redirect('link_up:events')
    # Ensure 'link_up:events' matches your actual events list URL name


@login_required
def my_events(request, year=datetime.now().year, month=datetime.now().strftime('%B')):
    # 1. Filter events the student is attending
    current_student_profile = request.user.student
    event_list = Event.objects.filter(
        attendees=current_student_profile).order_by('event_date')

    # ... (Reuse the existing calendar generation code and context) ...
    # You need to ensure all context variables (name, year, month, etc.) are defined here,
    # or you can consolidate the calendar logic into a helper function.

    # Example minimal context (you should include all variables your template needs):
    context = {
        'event_list': event_list,
        'name': request.user.first_name or request.user.username,
        # ... include calendar variables like 'year', 'month', 'cal', etc.
        'view_mode': 'my_events'  # Pass a flag to the template for button styling
    }

    return render(request, 'events.html', context)


@login_required
def all_events_student(request, year=datetime.now().year, month=datetime.now().strftime('%B')):
    # 1. Retrieve all events
    event_list = Event.objects.all().order_by('event_date')

    # ... (Reuse the existing calendar generation code and context) ...

    # Example minimal context:
    context = {
        'event_list': event_list,
        'name': request.user.first_name or request.user.username,
        # ... include calendar variables like 'year', 'month', 'cal', etc.
        'view_mode': 'all_events'  # Pass a flag to the template for button styling
    }

    return render(request, 'events.html', context)


@login_required
def attend_event(request, event_id):
    # Get the event or return a 404
    event = get_object_or_404(Event, pk=event_id)

    # Check if the user is a student
    if hasattr(request.user, 'student'):
        current_student = request.user.student

        # Add the student profile to the event's attendees list
        # The add() method on the M2M manager handles the inclusion.
        event.attendees.add(current_student)

    # Redirect the user back to the events list page (My Events or All Events)
    # Use the 'my-events' or 'all-events-student' name depending on where the user should go next.
    # Redirecting to My Events is usually logical
    return redirect('link_up:my-events')
