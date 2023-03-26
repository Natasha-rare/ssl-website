from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    last_name = models.CharField(_("last name"), max_length=150, blank=False)
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    fathername = models.CharField("Отчество", max_length=150, blank=True)
    image = models.ImageField(upload_to='users_images', null=True, blank=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    email = models.EmailField(_("email address"), blank=True)
    telegram = models.CharField("Ник в Телеграме", max_length=40, validators=[MinLengthValidator(5)], blank=False)

    STUDENT = 1
    MENTOR = 2

    ROLE_CHOICES = (
        (STUDENT, 'Участник'),
        (MENTOR, 'Ментор'),
    )

    role = models.PositiveSmallIntegerField("Статус", choices=ROLE_CHOICES, blank=False, null=True)
