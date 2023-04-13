from django.urls import path

# from users.views import login, registration, profile, logout
from .views import SignUp, profile_settings, logout

app_name = 'users'

urlpatterns = [
    path("signup/", SignUp.as_view(), name="signup"),
    path("logout/", logout, name="logout"),
    # path('verify/<str:email>/', emailVerification, name='email_verification'),
    path("profile_settings/", profile_settings, name="profile_settings"), #в дальнейшем изменится
]