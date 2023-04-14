from django.urls import path, include

# from users.views import login, registration, profile, logout
# from .views import SignUp, profile_settings, logout
from .views import UserViewSet, EmailVerificationView
from rest_framework.routers import DefaultRouter

app_name = 'users'
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path(r'verify/<str:email>/', EmailVerificationView.as_view(), name='email_verification'),
    path(r'', include(router.urls)),
    # path("signup/", SignUp.as_view(), name="signup"),
    # path("logout/", logout, name="logout"),
    # path("profile_settings/", profile_settings, name="profile_settings"), #в дальнейшем изменится
]