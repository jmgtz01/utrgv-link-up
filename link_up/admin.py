from .models import Event
from .models import Student
from .models import Venue
from django.contrib import admin
from .models import Computer, StudyRoom, Manager

@admin.register(Computer)
class ComputerAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "x", "y")
    list_editable = ("status", "x", "y")
    search_fields = ("name",)
    list_filter = ("status",)

@admin.register(StudyRoom)
class StudyRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "x", "y")
    list_editable = ("status", "x", "y")
    search_fields = ("name",)
    list_filter = ("status",)


admin.site.register(Venue)
admin.site.register(Student)
admin.site.register(Event)
admin.site.register(Manager)
