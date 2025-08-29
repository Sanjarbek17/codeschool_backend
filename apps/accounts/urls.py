from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication endpoints
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # Profile management
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path(
        "change-password/", views.ChangePasswordView.as_view(), name="change-password"
    ),
    # Group management
    path("groups/", views.GroupListCreateView.as_view(), name="group-list-create"),
    path("groups/<int:pk>/", views.GroupDetailView.as_view(), name="group-detail"),
    # Utility endpoints
    path("status/", views.user_status, name="user-status"),
]
