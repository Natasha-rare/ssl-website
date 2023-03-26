from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()

class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "fathername", "email", "role", "telegram")

class UserProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "fathername", "email", "role", "telegram", "image")