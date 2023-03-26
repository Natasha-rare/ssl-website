from django.urls import path

# from users.views import login, registration, profile, logout
from .views import registration, profile_settings, logout

app_name = 'users'

urlpatterns = [
    path("signup/", registration, name="signup"),
    path("logout/", logout, name="logout"),
    path("profile_settings/", profile_settings, name="profile_settings"), #в дальнейшем изменится
]