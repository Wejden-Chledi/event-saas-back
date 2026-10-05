# apps/inscriptions/apps.py
# apps/inscriptions/apps.py
from django.apps import AppConfig

class InscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inscriptions'

    def ready(self):
        pass