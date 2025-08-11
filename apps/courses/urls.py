from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'courses'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'lessons', views.LessonViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Additional custom endpoints can be added here
    # path('lessons/search/', views.LessonSearchView.as_view(), name='lesson-search'),
]
