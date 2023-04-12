import uuid

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model, password_validation
from django import forms
from django.core.validators import RegexValidator

User = get_user_model()

class RegistrationForm(UserCreationForm):
    # first_name = forms.CharField(
    #     widget=forms.TextInput(attrs={
    #     'class': 'form-control py-4', 'placeholder': 'Введите имя'}),
    #     label="Имя",
    #     required=True,
    #     # validators=[RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$', message="Разрешены только буквы")],
    #     error_messages={'errors': "Введите только буквы"}
    #     )
    # last_name = forms.CharField(required=True,
    #     widget=forms.TextInput(attrs={
    #     'class': 'form-control py-4', 'placeholder': 'Введите фамилию'}))
    # fathername = forms.CharField(required=False,
    #     widget=forms.TextInput(attrs={
    #     'class': 'form-control py-4', 'placeholder': 'Введите отчество'}))
    # telegram = forms.CharField(required=True,
    #     widget=forms.TextInput(attrs={
    #     'class': 'form-control py-4', 'placeholder': 'Введите ник в телеграмме (без @)'}))
    # email = forms.CharField(required=True,
    #     widget=forms.EmailInput(attrs={
    #     'class': 'form-control py-4', 'placeholder': 'Введите адрес эл. почты'}))
    # password1 = forms.CharField(required=True,
    #     widget=forms.PasswordInput(attrs={
    #     'class': 'form-control py-4', 'placeholder': 'Введите пароль'}))
    #     # help_text=password_validation.password_validators_help_text_html())
    # password2 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={
    #     'class': 'form-control py-4', 'placeholder': 'Подтвердите пароль'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'fathername', 'telegram', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.telegram = f'https://t.me/{self.cleaned_data["telegram"]}'
        print(user)
        if commit:
            user.save()
        print(user.telegram)

        # record = EmailVerification.objects.create(code=uuid.uuid4(), user=user)
        # record.send_verification_email()
        return user



class UserProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "fathername", "email", "telegram", "image")