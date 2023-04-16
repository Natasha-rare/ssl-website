import uuid

from django.contrib import auth
from django.contrib.auth import get_user_model, password_validation, authenticate
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics, views
from django_filters import rest_framework
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from django.http import HttpResponseRedirect
from django.urls import reverse
from json import JSONEncoder
from .models import EmailVerification
from .serializers import UserRegistrationSerializer,\
    SetNewPasswordSerializer, EmailVerificationSerializer, sendVerification, UserLoginSerializer, ResetPasswordEmailRequestSerializer, EmptySerializer
from django.core.mail import send_mail

User = get_user_model()

class UserAuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = EmptySerializer
    serializer_classes = {
        # 'login': UserLoginSerializer,
        'register': UserRegistrationSerializer,
        # 'password_change': ResetPasswordEmailRequestSerializer
    }

    @action(methods=['POST', ], detail=False)
    def register(self, request, *args, **kwargs):
        print('register here')
        user = request.data
        serializer = self.get_serializer(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        return Response(user_data, status=status.HTTP_201_CREATED)

    @action(methods=['POST', ], detail=False)
    @permission_classes([IsAuthenticated, ])
    def logout(self, request):
        print(request)
        auth.logout(request)
        return Response({"Success": "Logout Successfully"}, status=status.HTTP_200_OK)

    @action(methods=['POST', ], detail=False)
    def login(self, request):
        data = request.data
        email = data.get('email', None)
        password = data.get('password', None)
        user = authenticate(email=email, password=password)
        # print('jsjdjdjsjd', reverse('users:registration'))
        if user is not None:
            if user.is_verified_email and user.is_accepted:
                return Response({"Success": "Вход успешен", "data": data['email']}, status=status.HTTP_200_OK)  # redirect to index/profile
            elif user.is_accepted:
                return Response({"No active": "Ваша почта не подтверждена. Для подвтерждения прейдите по ссылке ..."},
                                status=status.HTTP_403_FORBIDDEN)
            elif user.is_verified_email:
                return Response({
                                    "Forbidden": "Вам отказано в доступе к клубу. Если вы хотите зарегистрироваться, напишите организатору ..."},
                                status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"No active": "Ваша почта не подтверждена и аккаунт не подтвержден"},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"Invalid": "Неверная почта или пароль"}, status=status.HTTP_404_NOT_FOUND)

    @action(methods=['POST', ], detail=False)
    def password_change(self, request):
        print(request.data["email"])
        email = request.data["email"]
        user = User.objects.filter(email=email)
        if user is not None:
            user = user.first()
            code = uuid.uuid4()
            link = reverse('users:password-reset-complete', kwargs={'email': user.email, 'code': code})
            verification_link = f'{settings.DOMAIN_NAME}{link}'
            subject = f'Сброс пароля для пользователя {user.first_name} {user.last_name}'
            message = 'Для подверждения сброса пароля для {} перейдите по ссылке: {} '.format(
                user.email,
                verification_link
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return Response({"message": "Письмо для сброса пароля было выслано на указанную почту"}, status=status.HTTP_200_OK)
        else:
            return Response({"Invalid": "Неверная почта"}, status=status.HTTP_404_NOT_FOUND)

    def get_serializer_class(self):
        if not isinstance(self.serializer_classes, dict):
            raise ImproperlyConfigured("serializer_classes should be a dict mapping.")

        if self.action in self.serializer_classes.keys():
            return self.serializer_classes[self.action]
        return super().get_serializer_class()

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


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request, **kwargs):
        print(request.data)
        password = request.data.get("password")
        email = kwargs["email"]
        serializer = self.serializer_class(data={"password": password, "email":email})
        print(serializer)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)


class EmailVerificationView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer

    def send_verification(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email)
        print(user)
        if user.exists():
            if user[0].is_accepted:
                try:
                    sendVerification(email)
                    return Response({"Success": "Код подтверждения был выслан на вашу почту"}, status=status.HTTP_200_OK)
                except Exception as error:
                    return Response({"Error": error})
            else:
                return Response({"Forbidden": "Вам отказано в доступе к клубу. Если вы хотите зарегистрироваться, напишите организатору ..."},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"Invalid": "Неверная почта"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, **kwargs):
        if 'email' not in kwargs:
            return self.send_verification(request)
        print(kwargs['email'])
        code = request.data['code']
        user = get_object_or_404(User, email=kwargs['email'])
        print(user)
        email_verifications = EmailVerification.objects.filter(user=user)
        serializer = UserRegistrationSerializer(user)
        if email_verifications.exists() and not email_verifications.first().is_expired():
            user.is_verified_email = True
            print(user.is_verified_email)
            user.save()
            # HttpResponseRedirect
            return Response({"Success": f"Ваша заявка на участие в клубе успешно принята. Ожидайте ответ в течении трёх дней. Результат рассмотрения заявки придет на {kwargs['email']}."}, status=status.HTTP_200_OK)
        elif email_verifications.first().is_expired():
            return Response({"Error": "Действие кода подтверждения истекло. Для получения нового кода перейдите по ссылке ..."}, status=status.HTTP_403_FORBIDDEN)
        if not user.is_accepted:
            return Response({"Forbidden": "Вам отказано в доступе к клубу. Если вы хотите зарегистрироваться, напишите организатору ..."},
                                status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.data, status=status.HTTP_406_NOT_ACCEPTABLE)



class ProfileView(viewsets.ModelViewSet):
    pass


