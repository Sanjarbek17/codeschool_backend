from django.urls import path
from . import views

urlpatterns = [
    path("webhook/", views.webhook, name="telegram_webhook"),
    path("set-webhook/", views.set_webhook, name="set_webhook"),
]
