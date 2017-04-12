from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from djmoney.models.fields import MoneyField
from moneyed import Money
from bananas.models import TimeStampedModel, UUIDModel
from enumfields import EnumIntegerField
from . import enums
from .signals.signals import status_change
from utils.enums import validate_transition


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

    def _latest_stamps(self):
        # Filter out the latest status timestamps for every transaction
        stamps = self.annotate(latest_stamp=models.Max('states__date_created'))
        return stamps.values_list('latest_stamp', flat=True)

    def by_status(self, status=None):
        status_query = {}
        if status is not None:
            status_query = {'states__status': status}
        qs = self.filter(
            states__date_created__in=self._latest_stamps(),
            **status_query
        )
        return qs

    def countable(self):
        return self.filter(
            (Q(amount__lt=0) & Q(states__status=enums.TrxStatus.PENDING))
            | (Q(amount__gte=0) & Q(states__status=enums.TrxStatus.FINALIZED)),
        ).exclude(
            # Exclude the ones that have CANCELLATION as last status
            Q(states__status=enums.TrxStatus.CANCELLATION),
            states__date_created__in=self._latest_stamps()
        )

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
    reference = models.CharField(max_length=128, blank=True, null=True)

    objects = WalletTrxsQuerySet.as_manager()

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')

    @property
    def status(self):
        # As a transaction should never _not_ be in a state, we want
        # latest to throw an exception when this does not happen
        state = self.states.latest('date_created')
        return state.status

    def set_status(self, status):
        state = self.states.order_by('-date_created').first()

        validate_transition(
            enums.TrxStatus,
            from_state=state.status if state is not None else state,
            to_state=status
        )
        status_obj = self.states.create(status=status)

        currency = self.wallet.currency
        if self.amount < Money(0, currency or settings.DEFAULT_CURRENCY):
            direction = enums.TrxDirection.OUTGOING
        else:
            direction = enums.TrxDirection.INCOMING

        # It looks weird that we're faking sending the signal from
        # WalletTransactionStatus
        status_change.send(
            sender=status_obj.__class__,
            instance=status_obj,
            from_status=state.status if state is not None else state,
            to_status=status,
            direction=direction
        )


class WalletTransactionStatus(UUIDModel, TimeStampedModel):
    trx = models.ForeignKey('WalletTransaction', related_name='states')
    status = EnumIntegerField(
        enums.TrxStatus,
        verbose_name=_('type'),
        default=enums.TrxStatus.PENDING
    )

    @property
    def signed_amount(self):
        """Returns the amount in a signed form based on the trx type"""
        if self.status == enums.TrxStatus.CANCELLATION:
            return -self.trx.amount

        return self.trx.amount

    @property
    def countable(self):
        """Returns a boolean depending on if the transactions counts or not.

        For example, rejected transactions do not contribute to the wallet
        balance.
        """
        currency = self.trx.wallet.currency
        if self.trx.amount < Money(0, currency or settings.DEFAULT_CURRENCY):
            # Outgoing
            return self.status in (enums.TrxStatus.PENDING,
                                   enums.TrxStatus.CANCELLATION)
        else:
            # Incoming
            return self.status in (enums.TrxStatus.FINALIZED,)

    class Meta:
        unique_together = ('trx', 'status')
        ordering = ('-date_created',)
        verbose_name = _('transaction status')
        verbose_name_plural = _('transaction statuses')
