from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from core import settings

# Swagger/OpenAPI Schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="CodeSchool Backend API",
        default_version='v1',
        description="""
        ## CodeSchool Backend API Documentation
        
        This is the comprehensive API documentation for the CodeSchool learning management system.
        
        ### Authentication
        Most endpoints require authentication using Token-based authentication.
        
        #### How to authenticate:
        1. Register a new account or login with existing credentials via `/api/auth/register/` or `/api/auth/login/`
        2. Copy the token from the response
        3. Click the "Authorize" button above and enter: `Token YOUR_TOKEN_HERE`
        4. You can now access protected endpoints
        
        ### API Sections
        - **Authentication**: User registration, login, profile management
        - **Courses**: Course management and enrollment
        - **Assignments**: Assignment creation and management
        - **Submissions**: Student assignment submissions
        - **Progress**: Learning progress tracking
        - **Editor**: Code editor functionality
        
        ### User Types
        - **Teachers**: Can create courses, assignments, and manage students
        - **Students**: Can enroll in courses, submit assignments, and track progress
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@codeschool.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API endpoints
    path("api/auth/", include("apps.accounts.urls")),
    path("api/courses/", include("apps.courses.urls")),
    path("api/assignments/", include("apps.assignments.urls")),
    path("api/progress/", include("apps.progress.urls")),
    path("api/submissions/", include("apps.submissions.urls")),
    
    # Editor endpoints
    path("editor/", include("apps.editor.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
