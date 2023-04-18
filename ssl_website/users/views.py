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
from .permissions import ReadOnlyPermission, ArbitratorPermission, AdminPermission, StudentPermission
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.urls import reverse
from json import JSONEncoder
from .models import EmailVerification
from .serializers import UserRegistrationSerializer, \
    SetNewPasswordSerializer, EmailVerificationSerializer, sendVerification, \
    UserSerialiser, EmptySerializer, UserAllSerializer, PasswordChangeSerializer
from django.core.mail import send_mail

User = get_user_model()

class UserAuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

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

    # def send_verification(self, request):
    #     email = request.data.get("email")
    #     user = User.objects.filter(email=email)
    #     print(user)
    #     if user.exists():
    #         if user[0].is_accepted:
    #             try:
    #                 sendVerification(email)
    #                 return Response({"Success": "Код подтверждения был выслан на вашу почту"}, status=status.HTTP_200_OK)
    #             except Exception as error:
    #                 return Response({"Error": error})
    #         else:
    #             return Response({"Forbidden": "Вам отказано в доступе к клубу. Если вы хотите зарегистрироваться, напишите организатору ..."},
    #                             status=status.HTTP_403_FORBIDDEN)
    #     else:
    #         return Response({"Invalid": "Неверная почта"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, **kwargs):
        if 'email' not in kwargs:
            sendVerification(request.data.get("email"))
            return Response({"Success": "Код подтверждения был выслан на вашу почту"}, status=status.HTTP_200_OK)
        print(kwargs['email'])
        code = request.data['code']
        user = get_object_or_404(User, email=kwargs['email'])
        print(user)
        email_verifications = EmailVerification.objects.filter(user=user)
        serializer = UserRegistrationSerializer(user)
        if email_verifications.exists() and not email_verifications.last().is_expired() \
                and email_verifications.last().code == code:
            user.is_verified_email = True
            user.save()
            if user.is_accepted:
                return Response({"Success": "Ваша почта успешно обновлена"})
            # HttpResponseRedirect
            return Response({"Success": f"Ваша заявка на участие в клубе успешно принята. Ожидайте ответ в течении трёх дней. Результат рассмотрения заявки придет на {kwargs['email']}."}, status=status.HTTP_200_OK)
        elif email_verifications.first().is_expired():
            return Response({"Error": "Действие кода подтверждения истекло. Для получения нового кода перейдите по ссылке ..."}, status=status.HTTP_403_FORBIDDEN)
        if not user.is_accepted:
            return Response({"Forbidden": "Вам отказано в доступе к клубу. Если вы хотите зарегистрироваться, напишите организатору ..."},
                                status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.data, status=status.HTTP_406_NOT_ACCEPTABLE)


class PasswordChangeView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = PasswordChangeSerializer
    permission_classes = [StudentPermission| AdminPermission| ArbitratorPermission ]

    def update(self, request, *args, **kwargs):
        print(request.user.role)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"Changed": "Пароль изменен успешно!!!"}, status=status.HTTP_200_OK)


class ProfileView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = EmptySerializer
    serializer_classes = {
        'profile': UserSerialiser,
        'users_all': UserAllSerializer
    }
    # permission_classes = [StudentPermission, AdminPermission, ArbitratorPermission]

    @action(methods=['GET', 'PATCH', ], detail=False)
    @permission_classes([StudentPermission, AdminPermission, ArbitratorPermission,])
    def profile(self, request):
        user = get_object_or_404(User, email=request.user.email)
        if request.method == "GET":
            serializer = self.get_serializer(user, many=False)
            return Response(serializer.data)
        if request.method == "PATCH":
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)


    @action(methods=['GET', ], detail=False, permission_classes=[AdminPermission, ])
    def users_all(self, request):
        if request.method == "GET":
            users = User.objects.all()
            try:
                serializer = self.get_serializer(users, many=True)
                print(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except:
                serializer.is_valid()
                return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if not isinstance(self.serializer_classes, dict):
            raise ImproperlyConfigured("serializer_classes should be a dict mapping.")

        if self.action in self.serializer_classes.keys():
            return self.serializer_classes[self.action]
        return super().get_serializer_class()
