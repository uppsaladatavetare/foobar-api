"""
Django settings for foobar project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""
import datetime
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY',
                       '%^5x9&idy09abn3my1)p+9_g!=aglt4&qog*5ztxwc@xjjp0m%')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', True)
TEMPLATE_DEBUG = os.getenv('TEMPLATE_DEBUG', True)

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')


# Application definition
INSTALLED_APPS = (
    'shop',
    'wallet',
    'foobar',
    'authtoken',

    'rest_framework',
    'rest_framework_swagger',

    'raven.contrib.django.raven_compat',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'foobar.urls'

WSGI_APPLICATION = 'foobar.wsgi.application'


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': ('raven.contrib.django.raven_compat.'
                      'handlers.SentryHandler'),
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
from bananas.url import database_conf_from_url
default_db = 'sqlite3://{}'.format(os.path.join(BASE_DIR, 'db.sqlite3'))
db_config = database_conf_from_url(os.getenv('DJANGO_DB', default_db))

DATABASES = {
    'default': db_config
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = os.getenv('STATIC_ROOT', os.path.join(BASE_DIR, 'static'))
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASS': (
        'rest_framework.permissions.IsAdminUser',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'authtoken.authentication.TokenAuthentication',
    ),
}

API_TOKEN_SCOPES = (
    ('read', 'Read scope'),
    ('write', 'Write scope'),
    ('accounts', 'Access to accounts'),
    ('categories', 'Access to categories'),
    ('products', 'Access to products'),
    ('purchases', 'Ability to make purchases'),
    ('wallet_trxs', 'Access to wallet transactions'),
    ('wallets', 'Access to wallets'),
)

# Raven config
RAVEN_CONFIG = {
    'dsn': os.getenv('SENTRY_DSN'),
}

# Foobar configuration
DEFAULT_CURRENCY = 'SEK'
CURRENCY_CHOICES = (
    ('SEK', 'SEK'),
)
CURRENCIES = [c[0] for c in CURRENCY_CHOICES]
FOOBAR_MAIN_WALLET = os.getenv('FOOBAR_MAIN_WALLET',
                               'ae912470-b9d2-4c53-85e9-4af9ef35a2a1')
FOOBAR_CASH_WALLET = os.getenv('FOOBAR_CASH_WALLET',
                               '1c61f916-a251-4dc0-a842-01aa2dee73f8')
PURCHASE_CANCEL_MAX_DELTA = datetime.timedelta(minutes=15)

# Thunderpush connection
THUNDERPUSH_HOST = os.getenv('THUNDERPUSH_HOST', 'localhost:8080')
THUNDERPUSH_APIKEY = os.getenv('THUNDERPUSH_APIKEY', 'foobar')
THUNDERPUSH_PROTO = os.getenv('THUNDERPUSH_PROTO', 'http')

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.debug',
    'django.template.context_processors.i18n',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.template.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'foobar.context_processors.thunderpush_settings',
]
