from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import serializers
import datetime
from django.contrib.auth.password_validation import validate_password
import uuid
from datetime import timedelta
from django.utils.timezone import now
from rest_framework.reverse import reverse_lazy
from .models import Cases, GameRegister, Game, Referee
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model, password_validation, authenticate, login
from django.core.mail import send_mail

User = get_user_model()
class GameRegistrationSerializer(serializers.ModelSerializer):
    all_time = serializers.BooleanField(required=False, label="Буду с 16:30 до 21:00")
    class Meta:
        model = GameRegister
        fields = ('all_time', 'begin_time', 'finish_time', 'player', 'attendance')

    def validate(self, attrs):
        if bool(attrs.get('all_time', 0)):
            return attrs
        if attrs['begin_time'] > attrs['finish_time'] or \
           not datetime.time(16, 30) <= attrs['begin_time'] <= datetime.time(21) or \
           not datetime.time(16, 30) <= attrs['finish_time'] <= datetime.time(21):
            raise serializers.ValidationError("Введенное время не валидно")
        return attrs

    def update(self, instance, validated_data):
        print(validated_data)
        instance.player = validated_data.get('player', instance.player)
        instance.begin_time = validated_data.get('begin_time', instance.begin_time)
        instance.finish_time = validated_data.get('finish_time', instance.finish_time)
        instance.attendance = validated_data.get('attendance', instance.attendance)
        instance.discuss_score = validated_data.get('discuss_score', instance.discuss_score)
        instance.conflict_score = validated_data.get('conflict_score', instance.conflict_score)
        instance.save()
        return instance

    def create(self, validated_data):
        if 'all_time' in validated_data:
            del validated_data['all_time']
        return GameRegister.objects.create(**validated_data)

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game