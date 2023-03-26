from django.shortcuts import render, HttpResponseRedirect
from django.contrib import auth, messages
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.views.generic import CreateView
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _

from django.core.mail import send_mail
from django.conf import settings

from .forms import RegistrationForm, UserProfileForm
from .models import User


def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()
            role = request.POST['role']
            user = User.objects.last()
            user.user_permissions.clear()
            if role == '1':
                group = Group.objects.get(name='Student')
                user.groups.add(group)
                group.user_set.add(user)
            elif role == '2':
                group = Group.objects.get(name='Mentor')
                group.user_set.add(user)
            return HttpResponseRedirect(reverse('users:profile_settings'))
    else:
        form = RegistrationForm()
    context = {'form': form}
    return render(request, 'signup.html', context)

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

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('index'))