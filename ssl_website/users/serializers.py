from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
import uuid
from datetime import timedelta
from django.utils.timezone import now
from .models import EmailVerification
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
                  'email', 'image', 'hse_pass')

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
        print(user)
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            print(User.objects.exclude(pk=user.pk).filter(email=value).exists())
            raise serializers.ValidationError({"email": "Пользователь с такой почтой уже существует"})
        return value

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name).capitalize()
        instance.last_name = validated_data.get('last_name', instance.last_name).capitalize()
        instance.father_name = validated_data.get('father_name', instance.father_name).capitalize()
        if instance.telegram != validated_data.get('telegram') and 'telegram' in validated_data:
            instance.telegram = f"https://t.me/{validated_data.get('telegram')}"
        instance.image = validated_data.get('image', instance.image)
        if instance.email != validated_data.get('email') and 'email' in validated_data:
            sendVerification(validated_data.get('email').lower(), kwargs={"email": instance.email})
            # instance.is_verified_email = False
            instance.email = validated_data.get('email').lower()
            # instance.save()
        instance.hse_pass = bool(validated_data.get("hse_pass", instance.hse_pass))
        instance.save()
        return instance


class UserAllSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=UserRole.choices,
        default=UserRole.USER,
    )
    
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'father_name', 'telegram',
                  'email', 'hse_pass', 'is_accepted', 'is_verified_email', 'role')
        read_only_fields = ('first_name', 'last_name', 'father_name', 'telegram',
                  'email')

    def update(self, instance, validated_data):
        instance.role = validated_data.get('role', instance.role)
        if instance.is_accepted != validated_data.get('is_accepted'):
            instance.is_accepted = validated_data.get('is_accepted', instance.is_accepted)
        #     send verification
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
                raise AuthenticationFailed("Ваша почта не подтверждена. Для подвтерждения прейдите по ссылке ...")
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
        user = User.objects.filter(telegram=f"https://t.me/{attrs['telegram']}")
        if user and user.is_verified_email:
            raise serializers.ValidationError({"telegram": "Пользователь с таким телеграмом уже существует."})
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        if 'image' in attrs:
            if attrs['image'].size > 10.0*1024*1024:
                raise serializers.ValidationError({"image": "Размер загруженного изображения больше 10мб"})
        if not attrs['accept_conditions']:
            # raise serializers.ValidationError({"conditions": "Для продолжения регистрации,необходимо принять условия пользовательского соглашения"})
            raise serializers.ValidationError({"conditions": "Для продолжения регистрации,необходимо принять условия пользовательского соглашения"})

        attrs['first_name'] = attrs['first_name'].capitalize()
        attrs['last_name'] = attrs['last_name'].capitalize()
        attrs['father_name'] = attrs['father_name'].capitalize()
        attrs['email'] = attrs['email'].lower()

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
        return user


def sendVerification(email, *args, **kwargs):
    user = User.objects.filter(email=email)
    if user.exists():
        print('sdfsfsf')
        user = user[0]
        expiration = now() + timedelta(hours=48)
        record = EmailVerification.objects.create(code=uuid.uuid4(), user=user, expiration=expiration)
        record.send_verification_email()
    elif 'email' in kwargs['kwargs']:
        print(kwargs)
        if User.objects.filter(email=kwargs['kwargs']['email']).exists():
            print('aaaaaaaadadadadaddada')
            user = User.objects.filter(email=kwargs['kwargs']['email']).first()
            user.is_verified_email = False
            user.email = email
            user.save()
            print(user)
            expiration = now() + timedelta(hours=48)
            record = EmailVerification.objects.create(code=uuid.uuid4(), user=user, expiration=expiration)
            record.send_verification_email()
    else:
        raise AuthenticationFailed('Пользователя с такой почтой не существует')


class EmailVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailVerification
        fields = ['code']


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, validators=[validate_password])
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('password', )
    def validate(self, attrs):
        try:
            password = attrs.get('password')
            email = attrs.get('email')
            user = User.objects.get(email=email)
            if user is not None:
                user.set_password(password)
                user.save()
                return user
            else:
                raise AuthenticationFailed('Пользователь с такой почтой не найден', 404)
        except Exception as e:
            print(e)
            raise AuthenticationFailed('Ссылка для сброса пароля не валидна', 401)

        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password1 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Старый пароль не верен')
        return value

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({'new_password2': "Новые пароли не совпадают"})
        validate_password(data['new_password1'], self.context['request'].user)
        return data

    def save(self, **kwargs):
        password = self.validated_data['new_password1']
        user = self.context['request'].user
        user.set_password(password)
        user.save()
        return user
