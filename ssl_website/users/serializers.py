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

    def validate_telegram(self, value):
        user = self.context['request'].user
        print('dfsdfs', user)
        if User.objects.exclude(pk=user.pk).filter(telegram=f"https://t.me/{value}").exists():
                raise serializers.ValidationError({"telegram": "Пользователь с таким телеграмом уже существует."})
        return value

    def validate_image(self, value):
        if value.size > 10.0*1024*1024:
            raise serializers.ValidationError({"image": "Размер загруженного изображения больше 10мб"})
        return value

    # change --------------------
    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError({"email": "Пользователь с такой почтой уже существует"})
        return value

    def update(self, instance, validated_data):
        user = self.context['request'].user

        if user.pk != instance.pk:
            raise serializers.ValidationError({"authorize": "У вас нет прав для редактирования данной записи"})
        print(instance)
        instance.first_name = validated_data.get('first_name', instance.first_name).capitalize()
        instance.last_name = validated_data.get('last_name', instance.last_name).capitalize()
        instance.father_name = validated_data.get('father_name', instance.father_name).capitalize()

        if 'telegram' in validated_data:
            instance.telegram = f"https://t.me/{validated_data.get('telegram')}"
        instance.image = validated_data.get('image', instance.image)
        if 'email' in validated_data:
            sendVerification(validated_data.get('email').lower(), kwargs={"email": instance.email})
            instance.email = validated_data.get('email').lower()
            # instance.save()
        instance.save()
        return instance

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


def sendVerification(email, *args, **kwargs):
    user = User.objects.filter(email=email)
    print(kwargs, kwargs['kwargs']['email'])
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
