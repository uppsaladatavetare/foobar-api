from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ShopConfig(AppConfig):
    name = 'shop'
    verbose_name = _('Shop')
    verbose_name_plural = _('Shops')

    def ready(self):
        from .signals import handlers  # noqa
