from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
@receiver(post_save, sender=User)
def user_accepted(sender, instance, created, **kwargs):
    print(sender)
    print(instance)
    print(created)
    print(kwargs)
    if not created and instance.is_accepted:
        send_mail(
            'Заявка принята',
            'Поздравляем, ваша заявка на участие в клубе принята! \n Теперь вы можете перейти в личный кабинет по ссылке http://127.0.0.1:8000/users/profile',
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=False,
        )
