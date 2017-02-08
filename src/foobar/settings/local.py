from .base import *
from bananas.url import database_conf_from_url

INTERNAL_IPS = ['127.0.0.1']
INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
