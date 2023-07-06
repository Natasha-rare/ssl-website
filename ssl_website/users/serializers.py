from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
import uuid
from datetime import timedelta
from django.utils.timezone import now
from rest_framework.reverse import reverse_lazy
from .models import EmailVerification
from django.conf import settings

User = get_user_model()
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model, password_validation, authenticate, login
from .models import UserRole
from django.core.mail import send_mail
class ChoicesField(serializers.Field):
    def __init__(self, choices, **kwargs):
        self._choices = choices
        super(ChoicesField, self).__init__(**kwargs)

    def to_representation(self, obj):
        return self._choices[obj]

    def to_internal_value(self, data):
        return getattr(self._choices, data)

class UserPwdChangeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    class Meta:
        model = User
        fields = ('email', )


class UserSerialiser(serializers.ModelSerializer):
    email = serializers.EmailField()
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'father_name', 'telegram',
                  'email', 'image', 'hse_pass', 'rating', 'game_status')
        read_only_fields = ('rating', 'game_status')
        extra_kwargs = {
            'father_name': {'required': False, 'validators': [RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$',
                                                                             message=_("Отчество неккоректно. Допустимые символы для ввода: пробел, латинские и киррилические буквы"))]},
            'first_name': {'validators': [RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$', message=_("Имя неккоректно. Допустимые символы для ввода: пробел, латинские и киррилические буквы"))]},
            'last_name': {'validators': [RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$', message=_("Фамилия неккоректна. Допустимые символы для ввода: пробел, латинские и киррилические буквы"))]},
        }

    def validate_telegram(self, value):
        user = self.context['request'].user
        print('dfsdfs', user)
        if User.objects.exclude(pk=user.pk).filter(telegram=f"https://t.me/{value}").exists():
                raise serializers.ValidationError({"telegram": "Пользователь с таким телеграмом уже существует."})
        return value

    def validate_image(self, value):
        if value:
            if value.size > 10.0*1024*1024:
                raise serializers.ValidationError({"image": "Размер загруженного изображения больше 10мб"})
        return value

    def validate_email(self, value):
        user = self.context['request'].user
        print(user, 'AHAHAHHA')
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            print(User.objects.exclude(pk=user.pk).filter(email=value).exists())
            raise serializers.ValidationError({"email": "Пользователь с такой почтой уже существует"})
        return value

    def update(self, instance, validated_data):
        print('i am going to upd this sh', validated_data)
        instance.first_name = validated_data.get('first_name', instance.first_name).capitalize()
        instance.last_name = validated_data.get('last_name', instance.last_name).capitalize()
        instance.father_name = validated_data.get('father_name', instance.father_name).capitalize()
        if instance.telegram != validated_data.get('telegram') and 'telegram' in validated_data:
            instance.telegram = f"https://t.me/{validated_data.get('telegram')}"
        instance.image = validated_data.get('image', instance.image)
        if instance.email != validated_data.get('email') and 'email' in validated_data:
            print('imhereagain')
            sendVerification(validated_data.get('email').lower(), kwargs={"email": instance.email})
            # instance.is_verified_email = False
            instance.email = validated_data.get('email').lower()
            # instance.save()
        # print(bool(validated_data.get("hse_pass", instance.hse_pass)), validated_data.get("hse_pass"))
        instance.hse_pass = bool(validated_data.get("hse_pass", instance.hse_pass))
        instance.save()
        return instance


# просмотр админом данных о пользователях и их изменение (не будет доступно в mvp)
class UserAllSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=UserRole.choices,
        default=UserRole.USER,
    )
    
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'father_name', 'telegram',
                  'email', 'hse_pass', 'is_accepted', 'is_verified_email', 'role')


    def update(self, instance, validated_data):
        instance.role = validated_data.get('role', instance.role)
        print('h1')
        if instance.is_accepted != validated_data.get('is_accepted') and 'is_accepted' in validated_data:
            instance.is_accepted = validated_data.get('is_accepted')
            if validated_data.get('is_accepted'):
                send_mail(
                    subject="Аккаунт подтвержден",
                    message=f"Здравствуйте, {instance.first_name} {instance.last_name}\n"
                            f"Администратор подтвердил Ваш аккаунт и теперь вы можете участвовать в играх \n"
                            f"Для перехода в личный кабинет, перейдите по ссылке {settings.DOMAIN_NAME}"
                            f"{reverse('users:profile-detail', kwargs={'pk': instance.pk})}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[instance.email],
                    fail_silently=False,
                )
            elif validated_data.get('is_accepted') is False:
                send_mail(
                    subject="Заявка отклонена",
                    message=f"Здравствуйте, {instance.first_name} {instance.last_name}\n"
                            f"К сожалению, ваша заявка отклонена и администратор пока не готов принять Вас в клуб",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[instance.email],
                    fail_silently=False,
                )
        instance.is_verified_email = validated_data.get('is_verified_email', instance.is_verified_email)
        instance.hse_pass = validated_data.get('hse_pass', instance.hse_pass)
        instance.save()
        return instance

class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    class Meta:
        model = User
        fields = ('email', 'password', )

    def validate(self, attrs):
        user = authenticate(email=attrs.get('email', ''), password=attrs.get('password', ''))
        # print(user, 'aaaaaaaaaa')
        if user:
            if user.is_verified_email and user.is_accepted:
                return attrs
            elif user.is_accepted:
                link = f"{settings.DOMAIN_NAME}{reverse('users:email-verification', kwargs={'email': attrs.get('email')})}"
                raise AuthenticationFailed(f"Ваша почта не подтверждена. Для подвтерждения прейдите по ссылке {link}")
            elif user.is_verified_email:
                raise AuthenticationFailed("Вам отказано в доступе к клубу. Если вы хотите зарегистрироваться, "
                                           "напишите организатору ...")
            else:
                raise AuthenticationFailed("Ваша почта не подтверждена и аккаунт не подтвержден модератором")
        else:
            raise AuthenticationFailed("Неверная почта или пароль")

        return {'email': user.email}

        return super().validate(attrs)

class EmptySerializer(serializers.Serializer):
    pass


class UserRegistrationSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url="media", required=False)
    accept_conditions = serializers.BooleanField(required=True, write_only=True)
    password1 = serializers.CharField(write_only=True, required=True, validators=[validate_password], label="Пароль")
    password2 = serializers.CharField(write_only=True, required=True, label="Повторите пароль")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'father_name', 'telegram',
                  'email', 'password1', 'password2', 'image', 'hse_pass', 'accept_conditions',)
        extra_kwargs = {
            'father_name': {'required': False, 'validators': [RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$',
                                                                        message=_("Отчество неккоректно."
                                                                "Допустимые символы для ввода: пробел, латинские и киррилические буквы"))]},
            'first_name': {'validators': [RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$',
                                                         message=_("Имя неккоректно. Допустимые символы для ввода: пробел, латинские и киррилические буквы"))]},
            'last_name': {'validators': [RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$',
                                                        message=_("Фамилия неккоректна. Допустимые символы для ввода: пробел, латинские и киррилические буквы"))]},
        }

    def validate(self, attrs):
        user = User.objects.filter(telegram=f"https://t.me/{attrs['telegram']}").last()
        if user and user.is_verified_email:
            raise serializers.ValidationError({"telegram": "Пользователь с таким телеграмом уже существует."})
        user = User.objects.filter(email=attrs['email'])
        if user and \
                user.is_validated_email:
            if not User.objects.filter(email=attrs['email']).is_accepted:
                raise serializers.ValidationError({'email': "Вы регестрировались раннее, но вам было отказано в доступе. "
                                                            "Для регистрации заново напишите ..."})
            raise serializers.ValidationError({'email': "Пользователь с такой почтой уже зарегистрирован"})
        else:
            attrs['email'] = attrs['email'].lower()
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        if 'image' in attrs:
            if attrs['image'].size > 10.0*1024*1024:
                raise serializers.ValidationError({"image": "Размер загруженного изображения больше 10мб"})
        if not attrs['accept_conditions']:
            raise serializers.ValidationError({"conditions": "Для продолжения регистрации,необходимо принять условия пользовательского соглашения"})

        attrs['first_name'] = attrs['first_name'].capitalize()
        attrs['last_name'] = attrs['last_name'].capitalize()
        attrs['father_name'] = attrs.get('father_name', '').capitalize()


        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            first_name=validated_data.get('first_name', None),
            last_name=validated_data.get('last_name', None),
            father_name=validated_data.get('father_name', None),
            email=validated_data.get('email', None),
            telegram=f"https://t.me/{validated_data.get('telegram', None)}",
            hse_pass=validated_data.get('hse_pass', None),
            image=validated_data.get('image', None)
        )
        user.set_password(validated_data['password1'])
        user.save()
        sendVerification(validated_data['email'])
        send_mail(
            subject="Регистрация нового пользователя",
            message=f"Зарегистрирован новый пользователь {user.first_name} {user.last_name}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        return user


def sendVerification(email, *args, **kwargs):
    # user = User.objects.get_object_or_504(email=email)
    try: # отправка письма при регистрации нового пользователя
        user = get_object_or_404(User, email=email)
        print(email, kwargs)
        # print('aaaaaaaadadadadaddada')
        print(user)
        expiration = now() + timedelta(hours=48)
        record = EmailVerification.objects.create(code=uuid.uuid4(), user=user, expiration=expiration)
        record.send_verification_email()
    except: # обновление почты через лк
        if kwargs:
            user = User.objects.filter(email=kwargs['kwargs']['email']).first()
            user.is_verified_email = False
            user.email = email
            user.save()
            subject = "Обновление почты"
            message = "Перейдите по ссылке для обновления почты: "
            print(user)
            expiration = now() + timedelta(hours=48)
            record = EmailVerification.objects.create(code=uuid.uuid4(), user=user, expiration=expiration)
            record.send_verification_email(subject=subject, message=message)
            return user
        raise AuthenticationFailed('Пользователя с такой почтой не существует')


class EmailVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailVerification
        fields = ['code']


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, validators=[validate_password])
    password2 = serializers.CharField(required=True, validators=[validate_password], write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('password', 'password2', )

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError({'password': "Новые пароли не совпадают"})
        email = attrs.get('email')
        user = User.objects.get(email=email)
        if user is not None:
            user.set_password(password)
            user.save()
            return user
        else:
            raise AuthenticationFailed('Пользователь с такой почтой не найден', 404)

        return attrs


