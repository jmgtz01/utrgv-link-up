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

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    # first_name = models.CharField(max_length=30)
    # last_name = models.CharField(max_length=30)
    # student_id = models.CharField(max_length=8)
    # email = models.EmailField('Student Email Address')
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True)
    student_id = models.CharField('Student ID', max_length=8)

    # def __str__(self):
    #     return self.first_name + ' ' + self.last_name

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name
    

class Manager(models.Model):
    # Links the Manager profile to the main user account
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True)

    # Add manager-specific fields here, if any
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.get_full_name()


class Event(models.Model):
    name = models.CharField('Event Name', max_length=120)
    event_date = models.DateTimeField('Event Date')
    venue = models.ForeignKey(
        Venue, blank=True, null=True, on_delete=models.CASCADE)
    # manager = models.CharField(max_length=60)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_events')
    email_address = models.EmailField('Email Address')
    description = models.TextField(blank=True)
    attendees = models.ManyToManyField(Student, blank=True)
    image_name = models.CharField(max_length=60)

    def __str__(self):
        return self.name


class Reservation(models.Model):
    RESOURCE_CHOICES = [
        ("computer", "Computer"),
        ("room", "Study Room"),
    ]

    resource_type = models.CharField(max_length=10, choices=RESOURCE_CHOICES)
    resource_id = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservations")
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["resource_type", "resource_id", "start", "end"]),
            models.Index(fields=["user", "start", "end"]),
        ]

    def __str__(self):
        start_str = self.start.strftime("%Y-%m-%d %H:%M")
        return f"{self.get_resource_type_display()} {self.resource_id} @ {start_str} for {self.user}"
