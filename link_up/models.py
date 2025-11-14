from django.db import models
from django.contrib.auth.models import User

# Create your models here.
COMPUTER_STATUSES = [
    ("available", "Available"),
    ("reserved",  "Reserved"),
    ("occupied",  "Occupied"),
    ("repair",    "Under Repair"),
]

ROOM_STATUSES = [
    ("available",    "Available"),
    ("reserved",     "Reserved"),
    ("occupied",     "Occupied"),
    ("out_of_order", "Out of Order"),
]

class Computer(models.Model):
    name = models.CharField(max_length=32, unique=True)
    x = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # left %
    y = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # top  %
    status = models.CharField(max_length=12, choices=COMPUTER_STATUSES, default="available")

    reserved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reserved_computers")

    def __str__(self):
        return f"{self.name} ({self.status})"


class StudyRoom(models.Model):
    name = models.CharField(max_length=32, unique=True)
    x = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    y = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=ROOM_STATUSES, default="available")

    reserved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reserved_rooms")

    def __str__(self):
        return f"{self.name} ({self.status})"


class Venue(models.Model):
    name = models.CharField('Venue Name', max_length=120)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=2)
    zip_code = models.CharField('Zip Code', max_length=5)
    phone = models.CharField('Contact Phone', max_length=14)
    web = models.URLField('Website Address', blank=True)
    email_address = models.EmailField('Email Address')

    def __str__(self):
        return self.name


class Student(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    student_id = models.CharField(max_length=8)
    email = models.EmailField('Student Email Address')

    def __str__(self):
        return self.first_name + ' ' + self.last_name


class Event(models.Model):
    name = models.CharField('Event Name', max_length=120)
    event_date = models.DateTimeField('Event Date')
    venue = models.ForeignKey(
        Venue, blank=True, null=True, on_delete=models.CASCADE)
    manager = models.CharField(max_length=60)
    description = models.TextField(blank=True)
    attendees = models.ManyToManyField(Student, blank=True)
    image_name = models.CharField(max_length=60)

    def __str__(self):
        return self.name
