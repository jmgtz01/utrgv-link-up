from django import forms
from django.forms import ModelForm
from .models import Venue, Event
from django.utils.html import format_html
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import User


# Define the custom validator for the phone format
phone_regex = RegexValidator(
    regex=r'^\(\d{3}\) \d{3}-\d{4}$',
    message="Phone number must be entered in the format: (956) 123-4567."
)

utrgv_email_regex = RegexValidator(
    # Regex checks for user@utrgv.edu (case-insensitive checking is implied later)
    regex=r'^.+@utrgv\.edu$',
    # Your customized message
    message="The email address must belong to the UTRGV domain, ending with @utrgv.edu"
)

# Create a venue form


class VenueForm(ModelForm):
    class Meta:
        model = Venue
        fields = ('name', 'address', 'city', 'state',
                  'zip_code', 'phone', 'web', 'email_address')
        labels = {
            'name': format_html("Name: Enter Your Venue Here (<span style='color:red;'>Required</span>)"),
            'address': format_html("Address: Enter the Address (<span style='color:red;'>Required</span>)"),
            'city': format_html("City: Enter the City (<span style='color:red;'>Required</span>)"),
            'state': format_html("State: Enter the State (<span style='color:red;'>Required</span>)"),
            'zip_code': format_html("Zip code: Enter the zip code (<span style='color:red;'>Required</span>)"),
            'phone': format_html("Phone: Enter the phone number (<span style='color:red;'>Required</span>)"),
            'web': format_html("Web: Enter the web address"),
            'email_address': format_html("Email address: Enter email address (<span style='color:red;'>Required</span>)"),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UTRGV Venue Name'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345 UTRGV Drive'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brownsville'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TX'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '78586'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel', 'placeholder': '(956) 123-4567'}),
            'web': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'www.google.com'}),
            'email_address': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'john.doe01@utrgv.edu'}),
        }

    # --- Override the clean method for the 'state' field ---
    def clean_state(self):
        # 1. Get the current value from the cleaned data
        state = self.cleaned_data['state']

        # 2. Convert the state string to uppercase
        return state.strip().upper()

    # Override the 'phone' field to apply the validator
    phone = forms.CharField(
        validators=[phone_regex],
        max_length=14,  # (###) ###-#### is 14 characters
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'type': 'tel', 'placeholder': '(956) 123-4567'})
    )

    email_address = forms.EmailField(
        validators=[utrgv_email_regex],  # <-- ADDED THE REGEX VALIDATOR
        label=format_html(
            "Email address: Enter email address (<span style='color:red;'>Required</span>)"),
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': 'john.doe01@utrgv.edu'}),
    )

class EventForm(ModelForm):
    # This line defines a Field instance directly on the form
    event_date = forms.DateTimeField(
        label=format_html(
            "Date: Enter the Date (<span style='color:red;'>Required</span>)"),
        widget=forms.DateInput(attrs={
            'class':'form-control',
            'type':'datetime-local',
        },
            format='%Y-%m-%dT%H:%M'
        ),
    )

    venue = forms.ModelChoiceField(
        # This queryset fetches all available venues for the dropdown list
        queryset=Venue.objects.all(),
        label=format_html(
            "Venue: Pick your Venue (<span style='color:red;'>Required</span>)"),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="--- Select a Venue ---"
    )

    # def clean_manager(self):
    #     username = self.cleaned_data.get('manager')
    #     try:
    #         # Look up the User object based on the provided username
    #         manager_user = User.objects.get(username=username)
    #         # Return the User object required by the ForeignKey field
    #         return manager_user
    #     except User.DoesNotExist:
    #         raise forms.ValidationError(
    #             "User with that username does not exist.")

    manager = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label=format_html(
            "Manager: Pick the Manager (<span style='color:red;'>Required</span>)"),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    # def clean_image_name(self):
    #     """
    #     Prepends 'img/events-list/' to the image_name value if it exists and
    #     doesn't already start with the desired prefix.
    #     """
    #     image_name = self.cleaned_data.get('image_name')
    #     prefix = 'img/events-list/'

    #     if image_name:
    #         # Strip potential leading/trailing whitespace
    #         image_name = image_name.strip()

    #         # Check if the prefix is already there (case-insensitive for robustness)
    #         if not image_name.lower().startswith(prefix.lower()):
    #             return prefix + image_name

    #     return image_name
    
    class Meta:
        model = Event
        fields = ('name', 'event_date', 'venue', 'manager',
                  'email_address', 'description', 'image')
        labels = {
            'name': format_html("Name: Enter Your Event Here (<span style='color:red;'>Required</span>)"),
            # 'event_date': format_html("Date: Enter the Date (<span style='color:red;'>Required</span>)"),
            # 'venue': format_html("Venue: Pick your Venue (<span style='color:red;'>Required</span>)"),
            'manager': format_html("Manager: Enter the Manager's Username (<span style='color:red;'>Required</span>)"),
            'email_address': format_html("Email Address: Enter Event Contact Email (<span style='color:red;'>Required</span>)"),
            'description': format_html("Description code: Type a description of your event... (<span style='color:red;'>Required</span>)"),
            # 'attendees': format_html("Pick Attendees: (<span style='color:red;'>Required</span>)"),
            # 'image_name': format_html("Image Name: Enter the file name of your image"),
            'image': "Upload Event Image",
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UTRGV Event Name'}),
            # 'event_date': CustomSplitDateTimeWidget(date_format='%Y-%m-%d'),
            # 'venue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UTRGV CSCI'}),
            'manager': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'vaquero01'}),
            'email_address': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@utrgv.edu'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please joing us our anual UTRGV CSCI fair for fun activities, and food.'}),
            # 'attendees': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adrian Holovaty'}),
            'image_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'csci_fair_2025.jpg'}),
        }
