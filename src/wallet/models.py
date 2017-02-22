from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from djmoney.models.fields import MoneyField
from moneyed import Money
from bananas.models import TimeStampedModel, UUIDModel
from enumfields import EnumIntegerField
from . import enums


class WalletQuerySet(models.QuerySet):
    def sum(self, currency=None):
        amount = self.aggregate(balance=models.Sum('balance'))['balance']
        return Money(amount or 0, currency or settings.DEFAULT_CURRENCY)


class Wallet(UUIDModel):
    owner_id = models.CharField(max_length=128)
    balance = MoneyField(
        default=Money(0, settings.DEFAULT_CURRENCY),
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY
    )

    objects = WalletQuerySet.as_manager()

    class Meta:
        unique_together = ('owner_id', 'balance_currency',)

    @property
    def currency(self):
        return self.balance_currency


class WalletTrxsQuerySet(models.QuerySet):
    def outgoing(self):
        return self.filter(amount__lt=0)

    def incoming(self):
        return self.filter(amount__gt=0)

    def by_direction(self, direction):
        if direction == enums.TrxDirection.OUTGOING:
            return self.outgoing()
        else:
            return self.incoming()

    def countable(self):
        return self.exclude(trx_type=enums.TrxType.PENDING)

    def sum(self, currency=None):
        amount = self.aggregate(amount=models.Sum('amount'))['amount']
        return Money(amount or 0, currency or settings.DEFAULT_CURRENCY)

    def balance(self, currency=None):
        return self.countable().sum(currency)


class WalletTransaction(UUIDModel, TimeStampedModel):
    wallet = models.ForeignKey(Wallet, related_name='transactions')
    amount = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY,
        help_text=_('Positive amount to deposit money. '
                    'Negative amount to withdraw money.')
    )
    trx_type = EnumIntegerField(
        enums.TrxType,
        verbose_name=_('type'),
        default=enums.TrxType.FINALIZED
    )
    reference = models.CharField(max_length=128, blank=True, null=True)
    internal_reference = models.ForeignKey('self', blank=True, null=True)

    objects = WalletTrxsQuerySet.as_manager()

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')

    @property
    def signed_amount(self):
        """Returns the amount in a signed form based on the trx type"""
        return self.amount

    @property
    def countable(self):
        """Returns a boolean depending on if the transactions counts or not.

        For example, rejected transactions do not contribute to the wallet
        balance.
        """
        return self.trx_type != enums.TrxType.PENDING
