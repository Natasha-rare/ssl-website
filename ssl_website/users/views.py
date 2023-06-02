import uuid
from django.contrib import auth
from django.contrib.auth import get_user_model, password_validation, authenticate, login
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics, views

from .permissions import ReadOnlyPermission, ArbitratorPermission, AdminPermission, StudentPermission
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from json import JSONEncoder
from .models import EmailVerification
from .serializers import UserRegistrationSerializer, \
    SetNewPasswordSerializer, EmailVerificationSerializer, sendVerification, \
    UserSerialiser, EmptySerializer, UserAllSerializer, PasswordChangeSerializer, \
    UserLoginSerializer, UserPwdChangeSerializer
from django.core.mail import send_mail
from .models import UserRole
User = get_user_model()

class UserAuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = EmptySerializer
    serializer_classes = {
        'register': UserRegistrationSerializer,
        'password_change': UserPwdChangeSerializer,
        # 'users_all': UserAllSerializer
        'login': UserLoginSerializer
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

    @action(methods=['GET', ], detail=False)
    @permission_classes([IsAuthenticated, ])
    def logout(self, request):
        print(request)
        auth.logout(request)
        return Response({"Success": "Logout Successfully"}, status=status.HTTP_200_OK)

    @action(methods=['POST', ], detail=False)
    def login(self, request):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        login(request, User.objects.get(email=request.data['email']))
        return Response(serializer.data['email'], status=status.HTTP_200_OK)

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
class UserEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request, **kwargs):
        print(request.data)
        password = request.data.get("password")
        password2 = request.data.get("password2")
        email = kwargs["email"]
        serializer = self.serializer_class(data={"password": password, 'password2':password2,"email":email})
        print(serializer)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Пароль успешно обновлен'}, status=status.HTTP_200_OK)


class EmailVerificationView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer

    def get(self, request, **kwargs):
        sendVerification(kwargs['email'])
        return Response({"Success": "Код подтверждения был выслан на вашу почту"}, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        code = request.data['code']
        user = get_object_or_404(User, email=kwargs['email'])
        email_verifications = EmailVerification.objects.filter(user=user)
        serializer = UserRegistrationSerializer(user)
        # print(email_verifications.exists())
        # print(not email_verifications.last().is_expired())
        # print(email_verifications.last().code, code, str(email_verifications.last().code) == str(code))
        if email_verifications.exists() and (not email_verifications.last().is_expired()) \
                and (str(email_verifications.last().code) == str(code)):
            print('aaaaaaaaaapppp')
            user.is_verified_email = True
            user.save()
            if user.is_accepted:
                return Response({"Success": "Ваша почта успешно подтверждена"})
            # HttpResponseRedirect
            return Response({"Success": f"Ваша заявка на участие в клубе успешно принята. Ожидайте ответ в течении трёх дней. Результат рассмотрения заявки придет на {kwargs['email']}."}, status=status.HTTP_200_OK)
        elif email_verifications.first().is_expired():
            return Response({"Error": "Действие кода подтверждения истекло. Для получения нового кода перейдите по ссылке ..."}, status=status.HTTP_403_FORBIDDEN)
        elif not user.is_accepted:
            print('here')
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
        'retrieve': UserSerialiser,
        # 'update': UserSerialiser,
        # 'users_all': UserAllSerializer
        'list': UserAllSerializer
    }
    permission_classes = [StudentPermission | AdminPermission | ArbitratorPermission]


    def list(self, request):
        if request.user.role != UserRole.ADMIN:
            url = f"{settings.DOMAIN_NAME}{reverse_lazy('users:profile-list')}{request.user.pk}/"
            print(url)
            return HttpResponseRedirect(redirect_to=url)
        query_set = User.objects.all()
        return Response(self.get_serializer(query_set, many=True).data,
                        status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        if pk: pk = int(pk)
        if request.user.role != UserRole.ADMIN and request.user.pk != pk:
            return Response({"Error": "У вас нет доступа для просмотра данной страницы"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        try:
            instance = self.get_object()
        except:
            return Response({"Error": "Пользователь с таким id не найден"}, status=status.HTTP_404_NOT_FOUND)
        print(instance, 'retrieve')
        if request.user.role == UserRole.ADMIN:
            serializer = UserAllSerializer(instance)
        else:
            serializer = UserSerialiser(instance)
        serializer.data['telegram'] = serializer.data['telegram'].split('/')[-1]
        print(serializer.data['telegram'].split('/')[-1])
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    def update(self, request, pk=None, *args, **kwargs): #need to change
        if request.user.role == UserRole.ADMIN:
            user = get_object_or_404(User, pk=pk)
            serializer = UserAllSerializer(user, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            user = get_object_or_404(User, email=request.user.email)
            serializer = UserSerialiser(user, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            print(serializer)
            self.perform_update(serializer)
            return Response(serializer.data)

    def get_serializer_class(self):
        if not isinstance(self.serializer_classes, dict):
            raise ImproperlyConfigured("serializer_classes should be a dict mapping.")
        if self.action == 'update':
            if self.request.user.role == UserRole.ADMIN:
                return UserAllSerializer
            else:
                return UserSerialiser

        if self.action in self.serializer_classes.keys():
            return self.serializer_classes[self.action]
        return super().get_serializer_class()
