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

class UserSerialiser(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'father_name', 'telegram', 'email', 'password1', 'password2', 'hse_pass']
        extra_kwargs = {
            'father_name': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
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
            hse_pass=validated_data['hse_pass']
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