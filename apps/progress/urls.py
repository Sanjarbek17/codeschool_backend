from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HomeworkProgressViewSet, TaskProgressViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(r'homework-progress', HomeworkProgressViewSet, basename='homework-progress')
router.register(r'task-progress', TaskProgressViewSet, basename='task-progress')

app_name = 'progress'

urlpatterns = [
    path('', include(router.urls)),
]
