from django.db import models

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

    def __str__(self):
        return f"{self.name} ({self.status})"


class StudyRoom(models.Model):
    name = models.CharField(max_length=32, unique=True)
    x = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    y = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=ROOM_STATUSES, default="available")

    def __str__(self):
        return f"{self.name} ({self.status})"