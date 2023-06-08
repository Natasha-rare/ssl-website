from django.urls import path, include

# from users.views import login, registration, profile, logout
# from .views import SignUp, profile_settings, logout
from .views import UserAuthViewSet, EmailVerificationView, SetNewPasswordAPIView, ProfileView, PasswordChangeView
from rest_framework.routers import DefaultRouter

app_name = 'users'
router = DefaultRouter()
router.register('auth', UserAuthViewSet, basename="auth")
router.register('profile', ProfileView, basename="profile")
# print(router.urls)
urlpatterns = [
    path(r'verify_email/', EmailVerificationView.as_view(), name="resend-email"),
    path(r'verify_email/<str:email>/', EmailVerificationView.as_view(), name='email-verification'),
    path(r'users/', include(router.urls)),
    path(r'change_password/', PasswordChangeView.as_view(), name="password-change"), #change
    path('password_reset_complete/<str:email>/<code>/', SetNewPasswordAPIView.as_view(),
         name='password-reset-complete'), #change
    # path(r'profile/', ProfileView.as_view(), name="profile"),
    # path("signup/", SignUp.as_view(), name="signup"),
    # path("logout/", logout, name="logout"),
    # path("profile_settings/", profile_settings, name="profile_settings"), #в дальнейшем изменится
]
# print(urlpatterns)