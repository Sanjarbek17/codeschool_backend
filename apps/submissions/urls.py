from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HomeworkSubmissionViewSet, TestCaseViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(r'submissions', HomeworkSubmissionViewSet, basename='submission')
router.register(r'test-cases', TestCaseViewSet, basename='testcase')

app_name = 'submissions'

urlpatterns = [
    path('', include(router.urls)),
]
