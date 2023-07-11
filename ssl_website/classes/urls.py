from django.urls import path, include

# from users.views import login, registration, profile, logout
# from .views import SignUp, profile_settings, logout
from .views import GameRegistration
from rest_framework.routers import DefaultRouter

app_name = 'classes'
router = DefaultRouter()
router.register('game_register', GameRegistration, basename="game-registration")
# print(router.urls)
urlpatterns = [
    path(r'classes/', include(router.urls)),
]

print(urlpatterns)