# config/settings/test.py
from .base import *

DEBUG = True # Force le mode debug pour éviter les redirections de sécurité

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Désactiver absolument toutes les redirections de sécurité pour le pipeline
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
APPEND_SLASH = False  