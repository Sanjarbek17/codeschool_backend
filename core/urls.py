from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from core import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # API endpoints
    path("api/auth/", include("apps.accounts.urls")),
    path("api/courses/", include("apps.courses.urls")),
    path("api/assignments/", include("apps.assignments.urls")),
    path("api/progress/", include("apps.progress.urls")),
    path("api/submissions/", include("apps.submissions.urls")),
    
    # Editor endpoints
    path("editor/", include("apps.editor.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
