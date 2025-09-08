from django.urls import path
from .views import ExecuteCodeView, TestCodeView

app_name = "editor"

urlpatterns = [
    path("execute/", ExecuteCodeView.as_view(), name="execute_code"),
    path("test/", TestCodeView.as_view(), name="test_code"),
]
