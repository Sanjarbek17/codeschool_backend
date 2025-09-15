from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema

from core import settings


class CustomAutoSchema(SwaggerAutoSchema):
    """Custom schema to override default tagging by app name"""

    def get_tags(self, operation_keys=None):
        """Override tags to group by functionality instead of app name"""
        path = self.path
        method = self.method.lower()

        # Define custom tag mapping based on URL patterns
        if (
            path.startswith("/api/register")
            or path.startswith("/api/login")
            or path.startswith("/api/logout")
        ):
            return ["Authentication"]
        elif (
            path.startswith("/api/profile")
            or path.startswith("/api/change-password")
            or path.startswith("/api/status")
        ):
            return ["User Profile"]
        elif path.startswith("/api/groups"):
            return ["Groups Management"]
        elif path.startswith("/api/lessons"):
            return ["Lessons"]
        elif path.startswith("/api/attendance"):
            return ["Attendance"]
        elif path.startswith("/api/homework"):
            return ["Homework"]
        elif path.startswith("/api/tasks"):
            return ["Tasks"]
        elif path.startswith("/api/submissions") or path.startswith("/api/test-cases"):
            return ["Submissions"]
        elif path.startswith("/api/homework-progress") or path.startswith(
            "/api/task-progress"
        ):
            return ["Progress Tracking"]
        elif (
            path.startswith("/api/dashboard")
            or path.startswith("/api/students")
            or "teacher" in path
        ):
            return ["Teacher Management"]
        elif path.startswith("/editor/execute"):
            return ["Code Editor"]
        elif path.startswith("/editor/test"):
            return ["Code Testing"]
        else:
            # Fallback to default behavior for unmatched paths
            return super().get_tags(operation_keys)


# Swagger/OpenAPI Schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="CodeSchool Backend API",
        default_version="v1",
        description="""
        ## CodeSchool Backend API Documentation
        
        This is the comprehensive API documentation for the CodeSchool learning management system.
        
        ### Authentication
        Most endpoints require authentication using Token-based authentication.
        
        #### How to authenticate:
        1. Register a new account or login with existing credentials via `/api/register/` or `/api/login/`
        2. Copy the token from the response
        3. Click the "Authorize" button above and enter: `Token YOUR_TOKEN_HERE`
        4. You can now access protected endpoints
        
        ### API Sections
        - **Authentication**: User registration and login
        - **User Profile**: Profile management and settings
        - **Groups Management**: Student and teacher group management
        - **Lessons**: Course lessons and content
        - **Attendance**: Class attendance tracking
        - **Homework**: Homework assignments management
        - **Tasks**: Individual task management
        - **Submissions**: Assignment submission handling
        - **Progress Tracking**: Learning progress monitoring
        - **Code Editor**: Code execution functionality
        - **Code Testing**: Code testing and validation
        - **Teacher Management**: Teacher-specific operations
        
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
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # API endpoints
    path("api/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("api/", include(("apps.courses.urls", "courses"), namespace="courses")),
    path(
        "api/",
        include(("apps.assignments.urls", "assignments"), namespace="assignments"),
    ),
    path("api/", include(("apps.progress.urls", "progress"), namespace="progress")),
    path(
        "api/",
        include(("apps.submissions.urls", "submissions"), namespace="submissions"),
    ),
    path(
        "api/",
        include(("apps.teacher_mgmt.urls", "teacher_mgmt"), namespace="teacher_mgmt"),
    ),
    # Editor endpoints
    path("editor/", include(("apps.editor.urls", "editor"), namespace="editor")),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
