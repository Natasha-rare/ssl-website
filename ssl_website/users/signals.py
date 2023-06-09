from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import UserRole
from django.urls import reverse, reverse_lazy

User = get_user_model()

@receiver(pre_save, sender=User)
def user_accepted(sender, instance, **kwargs):
    if instance.pk is not None:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if instance.is_accepted and instance.role != UserRole.USER and not old_instance.is_accepted:
                # Send the acceptance email
                link = reverse_lazy('users:profile-list')
                profile_link = f'{settings.DOMAIN_NAME}{link}'
                send_mail(
                    'Заявка принята',
                    f'Поздравляем, ваша заявка на участие в клубе принята! \n Теперь вы можете перейти в личный кабинет по ссылке {profile_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.email],
                    fail_silently=False,
                )
            elif not instance.is_accepted and old_instance.is_accepted:
                # Send the rejection email
                send_mail(
                    'Заявка отклонена',
                    'К сожалению, заявка на участие в клубе отклонена. Оставайтесь на связи и не теряйте надежды на участие в клубе в дальнейшем.',
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.email],
                    fail_silently=False,
                )
        except User.DoesNotExist:
            pass


# @receiver(post_save, sender=User)
# def user_accepted(sender, instance, created, update_fields, **kwargs):
#     print(sender)
#     print(instance)
#     print(created, update_fields, 'ahaha')
#     if not created and instance.is_accepted and instance.role != UserRole.USER:
#         link = reverse_lazy('users:profile-list')
#         profile_link = f'{settings.DOMAIN_NAME}{link}'
#         send_mail(
#             'Заявка принята',
#             f'Поздравляем, ваша заявка на участие в клубе принята! \n Теперь вы можете перейти в личный кабинет по ссылке {profile_link}',
#             settings.DEFAULT_FROM_EMAIL,
#             [instance.email],
#             fail_silently=False,
#         )
#         instance.updated_by_admin = True
#     elif not instance.is_accepted and not kwargs['update_fields'] and instance.updated_by_admin:
#         send_mail(
#             'Заявка отклонена',
#             'К сожалению, заявка на участие в клубе отклонена. Оставайтесь на связи и не теряйте надежды на участие в клубе в дальнейшем.',
#             settings.DEFAULT_FROM_EMAIL,
#             [instance.email],
#             fail_silently=False,
#         )
#         instance.updated_by_admin = True
