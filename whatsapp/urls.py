from django.urls import path
from .views import send_template_message, whatsapp_webhook

app_name = "whatsapp"

urlpatterns = [
    path("send/", send_template_message, name="send_template_message"),
    path("webhook/", whatsapp_webhook, name="whatsapp_webhook"),
]
