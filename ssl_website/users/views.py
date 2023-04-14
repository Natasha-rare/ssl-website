from django.contrib.auth import get_user_model, password_validation
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics, views
from django_filters import rest_framework
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
import json
from json import JSONEncoder
from .models import EmailVerification
from .serializers import UserSerializer, EmailVerificationSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        return Response(user_data, status=status.HTTP_201_CREATED)

# @api_view(["POST"])
# @permission_classes([permissions.AllowAny])
# def send_email(request):
#     """Метод для отправки кода подтверждения на почту."""
#     serializer = EmailSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     email = serializer.data.get("email")
#     user, created = User.objects.get_or_create(email=email)
#     confirmation_code = default_token_generator.make_token(user)
#     # link = reverse('users:email_verification', kwargs={'email': self.user.email})
#     link = "/users"
#     verification_link = f'{settings.DOMAIN_NAME}{link}'
#     subject = f'Подверждение учетной записи для пользователя {user.first_name} {user.last_name}'
#     message = 'Ваш код подтверждения: {}.\n' \
#               ' Для подверждения учетной записи для {} перейдите по ссылке: {} '.format(
#         confirmation_code,
#         user.email,
#         verification_link
#     )
#     send_mail(
#         subject=subject,
#         message=message,
#         from_email=settings.EMAIL_HOST_USER,
#         recipient_list=[user.email],
#         fail_silently=False,
#     )
#     return Response("Код регистрации был выслан на ваш email")


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

# class SignUp(CreateView):
#     form_class = RegistrationForm
#     success_url = reverse_lazy("login")  # где login — это параметр "name" в path()
#     template_name = "signup.html"
#
#
# @login_required
# def profile_settings(request):
#     if request.method == 'POST':
#         form = UserProfileForm(instance=request.user, data=request.POST, files=request.FILES)
#         if form.is_valid():
#             form.save()
#             return HttpResponseRedirect(reverse('users:profile_settings'))
#         else:
#             print(form.errors)
#     else:
#         form = UserProfileForm(instance=request.user)
#     context = {
#         'form': form,
#     }
#     return render(request, "profile_settings.html", context)

class UserEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class EmailVerificationView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer

    def post(self, request, *args, **kwargs):
        print(kwargs['email'])
        code = request.GET['code']
        user = get_object_or_404(User, email=kwargs['email'])
        print(user)
        email_verifications = EmailVerification.objects.filter(user=user)
        serializer = UserSerializer(user)
        if email_verifications.exists() and not email_verifications.first().is_expired():
            user.is_verified_email = True
            print(user.is_verified_email)
            user.save()
            return Response({"message": "Почта была успешно подтверждена. Ждите ответа в ближайшие 3 дня"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.data, status=status.HTTP_406_NOT_ACCEPTABLE)

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
class LoginView(views.APIView):
    def post(self, request):
        data = request

# def logout(request):
#     auth.logout(request)
#     return HttpResponseRedirect(reverse('index'))
