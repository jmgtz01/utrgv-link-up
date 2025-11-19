from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
    first_name = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # --- NEW FIELD ---
    # Define choices again, or import them from the model if possible
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('manager', 'Manager'),
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='User Role'
    )

    # ADD THIS METHOD for email validation
    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Check if the email ends with the required domain (case-insensitive)
        if not email.lower().endswith('@utrgv.edu'):
            # Raise a ValidationError if the domain is incorrect
            raise forms.ValidationError(
                "You must register with a valid @utrgv.edu email address.")

        # If valid, return the cleaned data
        return email

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',
                  'email', 'password1', 'password2', 'user_type')
    
    def __init__(self, *args, **kwargs):
        super(RegisterUserForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        # 1. Get the user instance from the superclass save
        user = super().save(commit=False)

        # 2. Attach the user_type from cleaned data to the user instance
        # The signals will use this attribute later!
        user.user_type = self.cleaned_data['user_type']

        if commit:
            user.save()
        return user
