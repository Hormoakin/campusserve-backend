from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     os.environ.get("PGDATABASE", os.environ.get("POSTGRES_DB", "railway")),
        "USER":     os.environ.get("PGUSER", os.environ.get("POSTGRES_USER", "postgres")),
        "PASSWORD": os.environ.get("PGPASSWORD", os.environ.get("POSTGRES_PASSWORD", "")),
        "HOST":     os.environ.get("PGHOST", "localhost"),
        "PORT":     os.environ.get("PGPORT", "5432"),
    }
}

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
