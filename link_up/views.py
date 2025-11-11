from django.shortcuts import render
from .models import Computer, StudyRoom
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
import json
from .models import Computer, StudyRoom
from .models import COMPUTER_STATUSES, ROOM_STATUSES
from django.contrib.auth.decorators import login_required

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

    obj = (Computer if item_type == "computer" else StudyRoom).objects.filter(pk=pk).first()
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
        new_status = data["status"] # This is the *desired* new status
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
            obj.reserved_by = request.user # Admin reserves for themself
        else:
            obj.reserved_by = None # Any other status clears reservation
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
        is_mine = (c.reserved_by and c.reserved_by_id == request.user.id) # Use .id for efficiency
        
        # --- NEW LOGIC ---
        if c.status == "reserved":
            if is_mine:
                # It's my reservation, show green check
                d["icon"] = icon_map["computer"]["available"]
                d["status"] = "reserved" # JS needs to know it's "reserved"
            else:
                # Someone else's reservation, show lock
                d["icon"] = icon_map["computer"]["occupied"]
                d["status"] = "occupied" # Treat it as occupied for the user
        else:
            # It's available, repair, or occupied (by non-reservation)
            d["icon"] = icon_map["computer"][c.status]
        # --- END NEW LOGIC ---
            
        d["is_mine"] = is_mine # Send this to JavaScript
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
        "is_authenticated": request.user.is_authenticated # <-- THIS LINE IS NEW
    })

def study_groups(request):
    return render(request, 'study-groups.html', {})


def instant_message(request):
    return render(request, 'instant-message.html', {})


def events(request):
    return render(request, 'events.html', {})


def resources(request):
    return render(request, 'resources.html', {})
