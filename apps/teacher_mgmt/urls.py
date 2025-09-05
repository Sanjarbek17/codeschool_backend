from django.urls import path
from . import views

app_name = "teacher_mgmt"

urlpatterns = [
    # Teacher Dashboard
    path("dashboard/", views.TeacherDashboardView.as_view(), name="teacher-dashboard"),
    # Teacher Groups Management
    path("groups/", views.TeacherGroupsView.as_view(), name="teacher-groups"),
    path(
        "groups/<int:group_id>/",
        views.TeacherGroupDetailView.as_view(),
        name="teacher-group-detail",
    ),
    # Teacher Students Management
    path("students/", views.TeacherStudentsView.as_view(), name="teacher-students"),
]
