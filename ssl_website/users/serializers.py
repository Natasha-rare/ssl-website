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

class UserSerialiser(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'father_name', 'telegram',
                  'email', 'image', 'hse_pass')  # add password – ?

        extra_kwargs = {
            'father_name': {'required': False, 'validators': [RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$',
                                                                             message=_("Отчество неккоректно. Допустимые символы для ввода: пробел, латинские и киррилические буквы"))]},
            'first_name': {'validators': [RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$', message=_("Имя неккоректно. Допустимые символы для ввода: пробел, латинские и киррилические буквы"))]},
            'last_name': {'validators': [RegexValidator(r'^[a-zA-Zа-яА-Я\s]*$', message=_("Фамилия неккоректна. Допустимые символы для ввода: пробел, латинские и киррилические буквы"))]},
        }

    def validate(self, attrs):
        if 'telegram' in attrs:
            user = User.objects.filter(telegram=f"https://t.me/{attrs['telegram']}")
            if user:
                user = user.first()
                if self.context['request'].user != user:
                    raise serializers.ValidationError({"telegram": "Пользователь с таким телеграмом уже существует."})
            attrs['telegram'] = f"https://t.me/{attrs['telegram']}"
        if 'first_name' in attrs:
            attrs['first_name'] = attrs['first_name'].capitalize()
        if 'last_name' in attrs:
            attrs['last_name'] = attrs['last_name'].capitalize()
        if 'father_name' in attrs:
            attrs['father_name'] = attrs['father_name'].capitalize()
        return attrs


class UserAllSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'father_name', 'telegram',
                  'email', 'hse_pass', 'is_accepted', 'is_verified_email', 'role')
        read_only_fields = ('first_name', 'last_name', 'father_name', 'telegram',
                  'email')

class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', )


class EmptySerializer(serializers.Serializer):
    pass

class UserRegistrationSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url="media", required=False)
    accept_conditions = serializers.BooleanField(required=True)
    password1 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

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
        if user:
            raise serializers.ValidationError({"telegram": "Пользователь с таким телеграмом уже существует."})
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        if attrs['image'].size > 10.0*1024*1024:
            raise serializers.ValidationError({"image": "Размер загруженного изображения больше 10мб"})
        if not attrs['accept_conditions']:
            raise serializers.ValidationError({"conditions": "Для продолжения регистрации, "                                              "вы должны принять условия пользовательского соглашения"})
        attrs['first_name'] = attrs['first_name'].capitalize()
        attrs['last_name'] = attrs['last_name'].capitalize()
        attrs['father_name'] = attrs['father_name'].capitalize()
        attrs['email'] = attrs['email'].lower()
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            father_name=validated_data['father_name'],
            email=validated_data['email'],
            telegram=f"https://t.me/{validated_data['telegram']}",
            hse_pass=validated_data['hse_pass'],
            image=validated_data['image']
        )
        user.set_password(validated_data['password1'])
        user.save()
        sendVerification(validated_data['email'])
        return user


def sendVerification(email):
    user = User.objects.filter(email=email)
    if user.exists():
        user = user[0]
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
        return attr


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ['email']
