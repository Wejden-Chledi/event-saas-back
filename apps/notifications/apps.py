# apps/notifications/apps.py
# apps/notifications/apps.py
from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'

    def ready(self):
        # C'est ici que Django va lire ton fichier signals.py
        import apps.notifications.signals