from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
# Assuming Student and Manager models are in utrgv_link_up/models.py
from link_up.models import Student, Manager

# Retrieve the User model safely
User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Creates a Student or Manager profile upon User registration, 
    based on the 'user_type' attribute stored on the user instance.
    """
    if created:
        # Check if the user object has the 'user_type' attribute
        # which should be set by your registration form's save() method.
        user_type = getattr(instance, 'user_type', 'student')

        if user_type == 'student':
            Student.objects.create(user=instance)
        elif user_type == 'manager':
            Manager.objects.create(user=instance)
