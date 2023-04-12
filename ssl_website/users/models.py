from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

class UserRole(models.TextChoices):
    """Модель для роли пользователя."""

    USER = "user"  # просто зарегистрированный пользователь
    STUDENT = "student"  # просто зарегистрированный пользователь
    ARBITRATOR = "arbitrator"  # просто зарегистрированный пользователь
    ADMIN = "admin"  # просто зарегистрированный пользователь

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Users require an email field')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Модель для пользователя"""
    username = None  # сбрасываем username
    last_name = models.CharField(_("last name"),  max_length=150, blank=False)
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    fathername = models.CharField("Отчество", max_length=150, blank=True)
    image = models.ImageField(upload_to='users_images', null=True, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    telegram = models.CharField("Ник в Телеграме", max_length=100, validators=[MinLengthValidator(5)], blank=False)
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.USER,
        verbose_name="Роль",
    )
    tg_bot_id = models.CharField(_("id for telegram bot"), blank=True, max_length=40, null=True, default=None)
    is_accepted = models.BooleanField("Заявка принята", default=False, blank=False)
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

