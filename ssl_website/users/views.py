from django.shortcuts import render, HttpResponseRedirect
from django.contrib import auth, messages
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.views.generic import CreateView
from django.views.generic.base import TemplateView
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

from .forms import RegistrationForm, UserProfileForm

User = get_user_model()


# def registration(request):
#     if request.method == 'POST':
#         form = RegistrationForm(data=request.POST)
#         if form.is_valid():
#             form.save()
#             return HttpResponseRedirect(reverse('users:profile_settings'))
#     else:
#         form = RegistrationForm()
#     context = {'form': form}
#     return render(request, 'signup.html', context)

class SignUp(CreateView):
    form_class = RegistrationForm
    success_url = reverse_lazy("login")  # где login — это параметр "name" в path()
    template_name = "signup.html"


@login_required
def profile_settings(request):
    if request.method == 'POST':
        form = UserProfileForm(instance=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('users:profile_settings'))
        else:
            print(form.errors)
    else:
        form = UserProfileForm(instance=request.user)
    context = {
        'form': form,
    }
    return render(request, "profile_settings.html", context)

#
# def emailVerification(request, email):
#     # template_name = 'registration/email_verification.html'
#     #
#     # def get(self, request, *args, **kwargs):
#     #     user = User.objects.get(email=kwargs['email'])
#     #     email_verifications = EmailVerification.objects.filter(user=user)
#     #     if email_verifications.exists() and not email_verifications.first().is_expired():
#     #         user.is_verified_email = True
#     #         user.save()
#     #         return super(EmailVerificationView, self).get(request, *args, **kwargs)
#     #     else:
#     #         return HttpResponseRedirect(reverse('index'))
#     if request.method == 'POST':
#         form = EmailForm(data=request.POST)
#         if form.is_valid():
#             user = User.objects.get(email=email)
#             email_verifications = EmailVerification.objects.filter(user=user)
#             code = form.cleaned_data['code']
#             if email_verifications.exists() and not email_verifications.first().is_expired() \
#                     and code == email_verifications.first().code:
#                 user.is_verified_email = True
#                 user.save()
#             print(user)
#             return HttpResponseRedirect(reverse('users:profile_settings'))
#         else:
#             print(form.errors)
#     else:
#         form = EmailForm()
#     context = {
#         'form': form,
#     }
#     return render(request, "registration/email_verification.html", context)


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('index'))
