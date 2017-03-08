"""
WSGI config for foobar project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foobar.settings.local")

from raven.contrib.django.raven_compat.middleware.wsgi import Sentry  # NOQA
from django.core.wsgi import get_wsgi_application  # NOQA
application = Sentry(get_wsgi_application())
