from django import forms
from .models import UserApiCredentials, UserProfile
from django.contrib.auth.models import User

# Form for handling the API credentials (client_id, passcode, api_key, otp_secret_key)
class ApiDetailsForm(forms.ModelForm):
    class Meta:
        model = UserApiCredentials
        fields = ['client_id', 'passcode', 'api_key', 'otp_secret_key']
        widgets = {
            'client_id': forms.TextInput(attrs={'class': 'form-control'}),
            'passcode': forms.PasswordInput(attrs={'class': 'form-control'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'otp_secret_key': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Form for user login (username and passcode)
class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    passcode = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'class': 'form-control','autocomplete': 'off','title':'','data-toggle': 'tooltip', 'data-placement': 'top', 'data-original-title': 'Enter your passcode'}))    
