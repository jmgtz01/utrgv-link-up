from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import calendar
from calendar import HTMLCalendar
from datetime import datetime, time, timedelta
import json

from .models import (
    Computer,
    StudyRoom,
    COMPUTER_STATUSES,
    ROOM_STATUSES,
    Event,
    Venue,
    Reservation,
)
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
            Reservation.objects.filter(resource_type=item_type,
                                       resource_id=pk).delete()
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
    # Clean up expired reservations and release stale statuses
    cleanup_expired_reservations()
    now = timezone.localtime()

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
    active_comp_res = Reservation.objects.filter(
        resource_type="computer", end__gt=now).select_related("user")
    comp_res_map = {}
    for r in active_comp_res:
        if r.resource_id not in comp_res_map:
            comp_res_map[r.resource_id] = []
        comp_res_map[r.resource_id].append(r)

    for c in Computer.objects.order_by("name"):
        d = model_to_dict(c, fields=["id", "name", "x", "y", "status"])
        current_res_list = comp_res_map.get(c.id, [])
        current_res = next((r for r in current_res_list
                            if r.start <= now < r.end), None)
        is_mine = current_res and current_res.user_id == request.user.id

        if c.status == "repair":
            d["icon"] = icon_map["computer"]["repair"]
            d["status"] = "repair"
        elif current_res:
            d["status"] = "reserved" if is_mine else "occupied"
            d["icon"] = icon_map["computer"]["reserved" if is_mine else "occupied"]
        else:
            d["status"] = "available"
            d["icon"] = icon_map["computer"]["available"]

        d["is_mine"] = bool(is_mine)
        computers.append(d)

    rooms = []
    active_room_res = Reservation.objects.filter(
        resource_type="room", end__gt=now).select_related("user")
    room_res_map = {}
    for r in active_room_res:
        room_res_map.setdefault(r.resource_id, []).append(r)

    for r in StudyRoom.objects.order_by("name"):
        d = model_to_dict(r, fields=["id", "name", "x", "y", "status"])
        current_res_list = room_res_map.get(r.id, [])
        current_res = next((res for res in current_res_list
                            if res.start <= now < res.end), None)
        is_mine = current_res and current_res.user_id == request.user.id

        if r.status == "out_of_order":
            d["icon"] = icon_map["room"]["out_of_order"]
            d["status"] = "out_of_order"
        elif current_res:
            d["status"] = "reserved" if is_mine else "occupied"
            d["icon"] = icon_map["room"]["reserved" if is_mine else "occupied"]
        else:
            d["status"] = "available"
            d["icon"] = icon_map["room"]["available"]

        d["is_mine"] = bool(is_mine)
        rooms.append(d)

    return render(request, "available-computers.html", {
        "computers": computers,
        "rooms": rooms,
        "map_img": "img/secondfloor.png",
        "is_admin": request.user.is_staff,
        "is_authenticated": request.user.is_authenticated,  # <-- THIS LINE IS NEW
        "user_active": _active_reservation_for_user(request.user) if request.user.is_authenticated else None,
    })


def _active_reservation_for_user(user):
    now = timezone.localtime()
    res = Reservation.objects.filter(user=user, end__gt=now).order_by("start").first()
    if not res:
        return None
    # Fetch display name for resource
    Model = Computer if res.resource_type == "computer" else StudyRoom
    obj = Model.objects.filter(pk=res.resource_id).first()
    name = obj.name if obj else f"{res.resource_type.title()} #{res.resource_id}"
    return {
        "id": res.id,
        "resource_type": res.resource_type,
        "resource_id": res.resource_id,
        "resource_name": name,
        "start": timezone.localtime(res.start).isoformat(),
        "end": timezone.localtime(res.end).isoformat(),
    }


def _round_up_to_half_hour(dt):
    dt = dt.replace(second=0, microsecond=0)
    minute = dt.minute
    if minute == 0:
        return dt
    if minute <= 30:
        return dt.replace(minute=30)
    return (dt + timedelta(hours=1)).replace(minute=0)


def _round_down_to_half_hour(dt):
    dt = dt.replace(second=0, microsecond=0)
    minute = dt.minute
    if minute < 30:
        return dt.replace(minute=0)
    return dt.replace(minute=30)


def _cleanup_status_for_resource(model_cls, resource_type, now):
    # If a resource is marked reserved/occupied but has no live reservation, free it.
    stale = model_cls.objects.filter(
        status__in=["reserved", "occupied"],
        reserved_by__isnull=False
    )
    for obj in stale:
        has_active = Reservation.objects.filter(
            resource_type=resource_type,
            resource_id=obj.id,
            start__lte=now,
            end__gt=now
        ).exists()
        if not has_active:
            obj.status = "available"
            obj.reserved_by = None
            obj.save(update_fields=["status", "reserved_by"])


def cleanup_expired_reservations():
    now = timezone.localtime()
    Reservation.objects.filter(end__lte=now).delete()
    _cleanup_status_for_resource(Computer, "computer", now)
    _cleanup_status_for_resource(StudyRoom, "room", now)


@login_required
@require_POST
def cancel_reservation(request):
    cleanup_expired_reservations()
    now = timezone.now()
    active = Reservation.objects.filter(user=request.user, end__gt=now)
    count = active.count()
    for res in active:
        Model = Computer if res.resource_type == "computer" else StudyRoom
        obj = Model.objects.filter(pk=res.resource_id).first()
        if obj:
            obj.status = "available"
            obj.reserved_by = None
            obj.save(update_fields=["status", "reserved_by"])
    active.delete()
    return JsonResponse({"ok": True, "cleared": count})


@login_required
@require_POST
def available_slots(request):
    try:
        data = json.loads(request.body.decode())
        item_type = data["type"]
        pk = int(data["id"])
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    Model = Computer if item_type == "computer" else StudyRoom
    obj = Model.objects.filter(pk=pk).first()
    if not obj:
        return HttpResponseBadRequest("Not found")

    cleanup_expired_reservations()
    now = timezone.localtime()
    tz = timezone.get_current_timezone()
    today = now.date()
    day_start = timezone.make_aware(datetime.combine(today, time(8, 0)), tz)
    day_end = timezone.make_aware(datetime.combine(today, time(20, 0)), tz)

    start_at = max(day_start, _round_down_to_half_hour(now))
    reservations = list(Reservation.objects.filter(
        resource_type=item_type,
        resource_id=pk,
        end__gt=now
    ))
    is_free_now = not any(res.start <= now < res.end for res in reservations)

    slots = []
    cursor = start_at
    while cursor + timedelta(hours=1) <= day_end:
        end_cursor = cursor + timedelta(hours=1)
        overlap = any(res.start < end_cursor and res.end > cursor for res in reservations)
        slots.append({
            "start": cursor.isoformat(),
            "end": end_cursor.isoformat(),
            "available": not overlap,
        })
        cursor += timedelta(minutes=30)

    user_res = Reservation.objects.filter(user=request.user, end__gt=now).order_by("start").first()
    user_active = None
    if user_res:
        user_active = {
            "resource_type": user_res.resource_type,
            "resource_id": user_res.resource_id,
            "start": timezone.localtime(user_res.start).isoformat(),
            "end": timezone.localtime(user_res.end).isoformat(),
        }

    return JsonResponse({
        "slots": slots,
        "resource_name": obj.name,
        "resource_status": obj.status,
        "user_active": user_active,
        "current_available": is_free_now,
        "now": now.isoformat(),
    })


@login_required
@require_POST
def create_reservation(request):
    try:
        data = json.loads(request.body.decode())
        item_type = data["type"]
        pk = int(data["id"])
        reserve_now = data.get("reserve_now", False)
        start_str = data.get("start")
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    Model = Computer if item_type == "computer" else StudyRoom
    obj = Model.objects.filter(pk=pk).first()
    if not obj:
        return HttpResponseBadRequest("Not found")

    cleanup_expired_reservations()

    now_local = timezone.localtime()
    if reserve_now:
        start_dt = _round_down_to_half_hour(now_local)
        end_dt = start_dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        start_dt = parse_datetime(start_str)
        if not start_dt:
            return HttpResponseBadRequest("Invalid start time")
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
        start_dt = timezone.localtime(start_dt)
        end_dt = start_dt + timedelta(hours=1)

    today = timezone.localdate()
    if start_dt.date() != today:
        return HttpResponseBadRequest("Reservations must be for today")
    if start_dt.minute not in (0, 30):
        return HttpResponseBadRequest("Start must be on the hour or half-hour")

    tz = timezone.get_current_timezone()
    earliest = timezone.make_aware(datetime.combine(today, time(0, 0)), tz)
    latest_end = timezone.make_aware(datetime.combine(today, time(23, 59)), tz)
    if start_dt < earliest or end_dt > latest_end:
        return HttpResponseBadRequest("Outside reservable hours (8am-8pm)")

    now = timezone.localtime()
    if end_dt <= now:
        return HttpResponseBadRequest("Time slot has passed")

    # One active reservation across computers/rooms
    has_active = Reservation.objects.filter(user=request.user, end__gt=now).exists()
    if has_active:
        return HttpResponseBadRequest("You already have an active reservation.")

    # Block if resource is out of order/repair
    if getattr(obj, "status", "available") in ["repair", "out_of_order"]:
        return HttpResponseBadRequest("This spot is currently unavailable.")

    overlap = Reservation.objects.filter(
        resource_type=item_type,
        resource_id=pk,
        start__lt=end_dt,
        end__gt=start_dt
    ).exists()
    if overlap:
        return HttpResponseBadRequest("That slot is no longer available.")

    Reservation.objects.create(
        resource_type=item_type,
        resource_id=pk,
        user=request.user,
        start=start_dt,
        end=end_dt,
    )

    obj.status = "reserved"
    obj.reserved_by = request.user
    obj.save(update_fields=["status", "reserved_by"])

    return JsonResponse({"ok": True})


def study_groups(request):
    return render(request, 'media-equipment.html', {})


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
