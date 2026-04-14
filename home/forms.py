from django import forms
from .models import UserLocation

class LocationForm(forms.ModelForm):
    class Meta:
        model = UserLocation
        fields = ['address']