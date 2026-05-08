"""WSGI entrypoint for PythonAnywhere.

PA's WSGI file (linked from your Web tab) imports this `application` object.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
