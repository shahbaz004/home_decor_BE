from django.urls import path

from .views import (
    ChangePasswordView,
    CustomerListView,
    GoogleLoginView,
    LoginView,
    LogoutView,
    RegisterView,
    UserProfileView,
    VerifyEmailView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("verify-email/<str:key>/", VerifyEmailView.as_view(), name="verify_email"),
    path("google/", GoogleLoginView.as_view(), name="google_login"),
    path("customers/", CustomerListView.as_view(), name="customer_list"),
]
