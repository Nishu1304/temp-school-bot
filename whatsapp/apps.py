from django.apps import AppConfig


class WhatsappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "whatsapp"
    verbose_name = "WhatsApp Automation"

    def ready(self):
        """
        Runs when the app is loaded.
        You can import signals or initialize schedulers here later.
        """
        pass
