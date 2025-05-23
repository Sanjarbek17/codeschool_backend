"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import os
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf.urls.static import static

from core import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLUTTER_WEB_APP = os.path.join(BASE_DIR, "flutter_web")


def flutter_redirect(request, resource):
    return serve(request, resource, FLUTTER_WEB_APP)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("editor/", include("editor.urls")),
    path("bot/", include("handle_bot.urls")),  # Added bot URLs
    path("", lambda r: flutter_redirect(r, "index.html")),
    path("flutter_web/<path:resource>", flutter_redirect),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
