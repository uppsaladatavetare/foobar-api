from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class FoobarConfig(AppConfig):
    name = 'foobar'
    verbose_name = _('Foobar')

    def ready(self):
        from .signals import handlers  # noqa
