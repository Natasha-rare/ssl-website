from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import UserRole
from django.urls import reverse, reverse_lazy

User = get_user_model()
@receiver(post_save, sender=User)
def user_accepted(sender, instance, created, **kwargs):
    print(sender)
    print(instance)
    print(created)
    print(kwargs['update_fields'])
    if not created and instance.is_accepted and instance.role != UserRole.USER and not kwargs['update_fields']:
        link = reverse_lazy('users:profile-list')
        profile_link = f'{settings.DOMAIN_NAME}{link}'
        send_mail(
            'Заявка принята',
            f'Поздравляем, ваша заявка на участие в клубе принята! \n Теперь вы можете перейти в личный кабинет по ссылке {profile_link}',
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=False,
        )
    elif not instance.is_accepted and not kwargs['update_fields']:
        send_mail(
            'Заявка отклонена',
            'К сожалению, заявка на участие в клубе отклонена. Оставайтесь на связи и не теряйте надежды на участие в клубе в дальнейшем.',
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=False,
        )
