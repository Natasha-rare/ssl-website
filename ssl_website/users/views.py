from django.contrib import auth
from django.contrib.auth import get_user_model, password_validation, authenticate
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
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
from .serializers import UserRegistrationSerializer, EmailVerificationSerializer, sendVerification

User = get_user_model()

class UserRegisterView(generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

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

    def send_verification(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email)
        print(user)
        if user.exists():
            if user[0].is_accepted:
                try:
                    sendVerification(email)
                    return  Response({"Success": "Код подтверждения был выслан на вашу почту"}, status=status.HTTP_200_OK)
                except Exception as error:
                    return Response({"Error": error})
            else:
                return Response({ "Forbidden": "Вам отказано в доступе к клубу. Если вы хотите зарегистрироваться, напишите организатору ..."},
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
        if not user.is_accepted:
            return Response({"Forbidden": "Вам отказано в доступе к клубу. Если вы хотите зарегистрироваться, напишите организатору ..."},
                                status=status.HTTP_403_FORBIDDEN)
        if email_verifications.exists() and not email_verifications.first().is_expired():
            user.is_verified_email = True
            print(user.is_verified_email)
            user.save()
            # HttpResponseRedirect
            return Response({"Success": "Почта была успешно подтверждена. Ждите ответа в ближайшие 3 дня"}, status=status.HTTP_200_OK)
        elif email_verifications.first().is_expired():
            return Response({"Error": "Действие кода подтверждения истекло. Для получения нового кода перейдите по ссылке ..."}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(serializer.data, status=status.HTTP_406_NOT_ACCEPTABLE)



class LoginView(views.APIView):

    def post(self, request):
        data = request.data
        email = data.get('email', None)
        password = data.get('password', None)
        user = authenticate(email=email, password=password)
        print('jsjdjdjsjd', reverse('users:registration'))
        if user is not None:
            if user.is_verified_email and user.is_accepted:
                url = reverse('landing:index')
                return HttpResponseRedirect(url)
                # return Response({"Success": "Вход успешен", "data": data['email']}, status=status.HTTP_200_OK)  # redirect to index/profile
            elif user.is_accepted:
                return Response({"No active": "Ваша почта не подтверждена. Для подвтерждения прейдите по ссылке ..."}, status=status.HTTP_403_FORBIDDEN)
            elif user.is_verified_email:
                return Response({"Forbidden": "Вам отказано в доступе к клубу. Если вы хотите зарегистрироваться, напишите организатору ..."},
                                status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"No active": "Ваша почта не подтверждена и аккаунт не подтвержден"},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"Invalid": "Неверная почта или пароль"}, status=status.HTTP_404_NOT_FOUND)


class ProfileView(viewsets.ModelViewSet):
    pass

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated,])
def logout(request):
    print(request)
    auth.logout(request)
    # url = reverse('landing:index')
    return Response({"Success": "Logout Successfully"}, status=status.HTTP_200_OK)
