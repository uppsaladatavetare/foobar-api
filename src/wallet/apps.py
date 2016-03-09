from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WalletConfig(AppConfig):
    name = 'wallet'
    verbose_name = _('Wallet')
    verbose_name_plural = _('Wallets')

    def ready(self):
        from .signals import handlers  # noqa
