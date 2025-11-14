from django import forms
from django.forms import ModelForm
from .models import Venue
from django.utils.html import format_html
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

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
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UTRGV Events'}),
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
