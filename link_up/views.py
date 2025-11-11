from django.shortcuts import render
from .models import Computer, StudyRoom
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
import json
from .models import Computer, StudyRoom

@staff_member_required          # only allow staff to move markers
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

    # Precompute icon path for each item so the template is simple
    computers = []
    for c in Computer.objects.order_by("name"):
        d = model_to_dict(c, fields=["id", "name", "x", "y", "status"])
        d["icon"] = icon_map["computer"][c.status]
        computers.append(d)

    rooms = []
    for r in StudyRoom.objects.order_by("name"):
        d = model_to_dict(r, fields=["id", "name", "x", "y", "status"])
        d["icon"] = icon_map["room"][r.status]
        rooms.append(d)

    return render(request, "available-computers.html", {
        "computers": computers,
        "rooms": rooms,
        "map_img": "img/secondfloor.png",   # exact filename in your screenshot
    })


def study_groups(request):
    return render(request, 'study-groups.html', {})


def instant_message(request):
    return render(request, 'instant-message.html', {})


def events(request):
    return render(request, 'events.html', {})


def resources(request):
    return render(request, 'resources.html', {})
