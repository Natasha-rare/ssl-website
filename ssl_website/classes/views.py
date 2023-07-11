import json
import uuid
from django.contrib import auth
from django.contrib.auth import get_user_model, password_validation, authenticate, login
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from users.permissions import ReadOnlyPermission, ArbitratorPermission, AdminPermission, StudentPermission
from django.forms.models import model_to_dict
from rest_framework import viewsets, status, generics, views
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from json import JSONEncoder
from .models import Cases, GameRegister, Game, Referee, get_closest_game
from .serializers import *
from django.core.mail import send_mail
User = get_user_model()

# Create your views here.
class GameRegistration(viewsets.ModelViewSet):
    queryset = GameRegister.objects.all()
    serializer_class = GameRegistrationSerializer
    permission_classes_by_action = {
        'list': [AdminPermission | ArbitratorPermission],
        'create': [StudentPermission | ArbitratorPermission],
        'retrieve': [AdminPermission | ArbitratorPermission | StudentPermission],
        'update': [AdminPermission | ArbitratorPermission | StudentPermission],
        'destroy':[AdminPermission | ArbitratorPermission | StudentPermission],
    }
    # `create()`, `retrieve()`, `update()`,
    #     `partial_update()`, `destroy()` and `list()` actions.
    def list(self, request):
        game_day = get_closest_game()
        queryset = GameRegister.objects.filter(date=game_day)
        serializer = self.serializer_class(queryset, many=True)
        for obj in serializer.data:
            user = User.objects.filter(id=obj['player']).values()[0]
            user_show = user['image'], user['last_name'], user['first_name']
            obj['player'] = user_show
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = json.dumps(request.data)
        data = json.loads(data)
        if 'player' not in data:
            data.update({'player': request.user.id})
        serializer = self.serializer_class(data=data)
        print(serializer)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]