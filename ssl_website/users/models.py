from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import MinLengthValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.utils.timezone import now

class UserRole(models.TextChoices):
    """Модель для роли пользователя."""

    USER = "user"  # просто зарегистрированный пользователь
    STUDENT = "student"  # просто зарегистрированный пользователь
    ARBITRATOR = "arbitrator"  # просто зарегистрированный пользователь
    ADMIN = "admin"  # просто зарегистрированный пользователь


class User(AbstractUser):
    """Модель для пользователя"""
    last_name = models.CharField(_("last name"),  max_length=150, blank=False)
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    father_name = models.CharField("Отчество", max_length=150, blank=True)
    image = models.ImageField(upload_to='users_images', null=True, blank=True)
    email = models.EmailField(_("email address"), unique=True, blank=False)
    telegram = models.CharField("Ник в Телеграме", max_length=100, validators=[MinLengthValidator(5)], blank=False)
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.USER,
        verbose_name="Роль",
    )
    tg_bot_id = models.CharField(_("id for telegram bot"), blank=True, max_length=40, null=True, default=None)
    hse_pass = models.BooleanField("Есть пропуск в Вышку", default=False, blank=False)
    is_accepted = models.BooleanField("Заявка принята", default=False, blank=False)
    is_verified_email = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def clean(self):
        self.first_name = self.first_name.capitalize()
        self.last_name = self.last_name.capitalize()
        self.father_name = self.father_name.capitalize()
        self.email = self.email.lower()

#
# class EmailVerification(models.Model):
#     code = models.UUIDField(unique=True)
#     user = models.ForeignKey(to=User, on_delete=models.CASCADE)
#     created = models.DateTimeField(auto_now_add=True)
#     expiration = models.DateTimeField()
#
#     def __str__(self):
#         return f'EmailVerification object for {self.user.email}'
#
#     def send_verification_email(self):
#         link = reverse('users:email_verification', kwargs={'email': self.user.email})
#         verification_link = f'{settings.DOMAIN_NAME}{link}'
#         subject = f'Подверждение учетной записи для пользователя {self.user.first_name} {self.user.last_name}'
#         message = 'Ваш код подтверждения: {}.\n' \
#                   ' Для подверждения учетной записи для {} перейдите по ссылке: {} '.format(
#             self.code,
#             self.user.email,
#             verification_link
#         )
#         send_mail(
#             subject=subject,
#             message=message,
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[self.user.email],
#             fail_silently=False,
#         )
#
#     def is_expired(self):
#         return True if now() >= self.expiration else False
