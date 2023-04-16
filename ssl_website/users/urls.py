from django.urls import path, include

# from users.views import login, registration, profile, logout
# from .views import SignUp, profile_settings, logout
from .views import UserRegisterView, EmailVerificationView, LoginView, logout
from rest_framework.routers import DefaultRouter

app_name = 'users'
router = DefaultRouter()
# router.register(r'registration', UserRegisterViewSet, basename="registration")

urlpatterns = [
    path(r'login/', LoginView.as_view(), name="login"),
    path(r'logout/', logout, name="logout"),
    path(r'registration/', UserRegisterView.as_view(), name="registration"),
    path(r'verify_email/', EmailVerificationView.as_view(), name="resend_email"),
    path(r'verify_email/<str:email>/', EmailVerificationView.as_view(), name='email_verification'),
    path(r'users/', include(router.urls)),
    # path("signup/", SignUp.as_view(), name="signup"),
    # path("logout/", logout, name="logout"),
    # path("profile_settings/", profile_settings, name="profile_settings"), #в дальнейшем изменится
]