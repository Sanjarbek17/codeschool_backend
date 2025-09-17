from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"payments", views.PaymentViewSet)
router.register(r"students", views.StudentManagementViewSet)
router.register(r"teachers", views.TeacherManagementViewSet)
router.register(r"groups", views.GroupManagementViewSet)
router.register(r"courses", views.CourseManagementViewSet)

app_name = "admin_panel"

urlpatterns = [
    # Router URLs
    path("", include(router.urls)),
    # Custom endpoints
    path("dashboard/", views.AdminDashboardView.as_view(), name="dashboard"),
    path(
        "student-payment-summary/<int:student_id>/",
        views.StudentPaymentSummaryView.as_view(),
        name="student-payment-summary",
    ),
]
