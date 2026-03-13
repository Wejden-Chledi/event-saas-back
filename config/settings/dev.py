from .base import *
import os

DEBUG = True
ALLOWED_HOSTS = ["*"]

# DB dev
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "dev_db"),
        "USER": os.getenv("DB_USER", "dev_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "dev_pass"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": int(os.getenv("DB_PORT", 3306)),
        "OPTIONS": {
            "ssl": {
                "ca": os.path.join(BASE_DIR, "DigiCertGlobalRootG2.crt.pem"),
            }
        },
    }
}