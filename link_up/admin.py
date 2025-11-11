from django.contrib import admin
from .models import Computer, StudyRoom

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