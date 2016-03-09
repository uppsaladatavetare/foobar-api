from django.db import models
from django.conf import settings
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
    def pending_or_finalized(self):
        return self.filter(trx_status__in=[enums.TrxStatus.PENDING,
                                           enums.TrxStatus.FINALIZED])

    def pending(self):
        return self.filter(trx_status=enums.TrxStatus.PENDING)

    def finalized(self):
        return self.filter(trx_status=enums.TrxStatus.FINALIZED)

    def outgoing(self):
        return self.filter(trx_type=enums.TrxType.OUTGOING)

    def incoming(self):
        return self.filter(trx_type=enums.TrxType.INCOMING)

    def sum(self, currency=None):
        amount = self.aggregate(amount=models.Sum('amount'))['amount']
        return Money(amount or 0, currency or settings.DEFAULT_CURRENCY)

    def balance(self, currency=None):
        incoming = self.finalized().incoming().sum(currency)
        outgoing = self.pending_or_finalized().outgoing().sum(currency)
        return incoming - outgoing


class WalletTransaction(UUIDModel, TimeStampedModel):
    wallet = models.ForeignKey(Wallet, related_name='transactions')
    amount = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY
    )
    trx_type = EnumIntegerField(enums.TrxType)
    trx_status = EnumIntegerField(enums.TrxStatus)
    reference = models.CharField(max_length=128, blank=True, null=True)

    objects = WalletTrxsQuerySet.as_manager()

    @property
    def signed_amount(self):
        """Returns the amount in a signed form based on the trx type"""
        if self.trx_type == enums.TrxType.INCOMING:
            return self.amount
        else:
            return -self.amount

    @property
    def countable(self):
        """Returns a boolean depending on if the transactions counts or not.

        For example, rejected transactions does not contribute to
        the wallet balance.
        """
        if self.trx_type == enums.TrxType.INCOMING:
            return self.trx_status == enums.TrxStatus.FINALIZED
        else:
            return self.trx_status in [enums.TrxStatus.PENDING,
                                       enums.TrxStatus.FINALIZED]
