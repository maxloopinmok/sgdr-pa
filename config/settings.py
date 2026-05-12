"""Django settings for the PythonAnywhere-hosted public-facing app.

This is a presentation-only deployment: scraping happens on Max's laptop and
data is pushed in via the future ``/sync/`` endpoint. Hence the simpler,
single-file settings vs. the laptop's split base/production setup.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Read from PA's environment (set in the Web tab → Environment variables, or
# in the WSGI file). Don't ever commit secrets.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "set-DJANGO_SECRET_KEY-on-pythonanywhere"
)

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

# PA gives you <username>.pythonanywhere.com. Update this once you know yours.
ALLOWED_HOSTS = [h.strip() for h in os.environ.get(
    "DJANGO_ALLOWED_HOSTS", ".pythonanywhere.com,127.0.0.1,localhost"
).split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "https://*.pythonanywhere.com"
).split(",") if o.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "apps.companies",
    "apps.events",
    "apps.core",
    "apps.prices",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Whitenoise serves static files in production without needing a separate
    # web server config — perfect for PA.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# SQLite. The DB file lives next to manage.py so the laptop sync can replace
# it atomically (or push events in via the /sync/ endpoint).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-sg"
TIME_ZONE = "Asia/Singapore"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Cookies — secure since PA's URL is always HTTPS.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Analytics — GoatCounter (cookie-less, no consent banner needed).
# Sign up at goatcounter.com → pick a free subdomain like
# `sgdividendsreports.goatcounter.com` → set GOATCOUNTER_SITE_CODE here.
GOATCOUNTER_SITE_CODE = os.environ.get("GOATCOUNTER_SITE_CODE", "")

# Shared secret used by the laptop's sync push (future /sync/ endpoint).
# Generate a long random string and set it on PA's Environment Variables.
SYNC_SHARED_TOKEN = os.environ.get("SYNC_SHARED_TOKEN", "")
