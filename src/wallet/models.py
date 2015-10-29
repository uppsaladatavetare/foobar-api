from django.db import models
from django.conf import settings
from djmoney.models.fields import MoneyField, CurrencyField
from moneyed import Money
from bananas.models import TimeStampedModel, UUIDModel
from enumfields import EnumIntegerField
from . import enums


class Wallet(UUIDModel):
    owner_id = models.CharField(max_length=128)
    currency = CurrencyField(default=settings.DEFAULT_CURRENCY)

    class Meta:
        unique_together = ('owner_id', 'currency',)


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

    def sum(self):
        amount = self.aggregate(amount=models.Sum('amount'))['amount']
        return Money(amount or 0, settings.DEFAULT_CURRENCY)

    def balance(self):
        incoming = self.finalized().incoming().sum()
        outgoing = self.pending_or_finalized().outgoing().sum()
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
