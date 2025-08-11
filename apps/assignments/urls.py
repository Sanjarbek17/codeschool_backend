from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'assignments'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'homework', views.HomeworkViewSet)
router.register(r'tasks', views.TaskViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Additional custom endpoints can be added here
]
