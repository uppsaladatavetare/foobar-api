from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils import timezone
from enumfields import EnumIntegerField
from djmoney.models.fields import MoneyField
from bananas.models import UUIDModel, TimeStampedModel
from shop import api as product_api
from utils.models import ScannerField
from . import enums


class Account(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(User, null=True, blank=True)
    name = models.CharField(null=True, blank=True, max_length=128)
    email = models.EmailField(null=True, blank=True, unique=True)

    REQUIRED_FIELDS = (
        'name',
        'email',
    )

    @property
    def is_complete(self):
        return self.completeness == 1.0

    @property
    def completeness(self):
        values = [getattr(self, field, None) for field in self.REQUIRED_FIELDS]
        completed = [v for v in values if v]
        return len(completed) / len(self.REQUIRED_FIELDS)

    def __str__(self):
        return str(self.id)


class Card(UUIDModel, TimeStampedModel):
    account = models.ForeignKey(Account)

    # The card id is a uid from a mifare classic 1k card and is supposed
    # to be 8 bytes long.
    number = ScannerField(scanner='cards', unique=True, max_length=20)
    date_used = models.DateTimeField(null=True, blank=True)

    def clean(self):
        try:
            int(self.number)
        except ValueError:
            raise ValidationError(_('The card id should be an integer.'))

    def __str__(self):
        return 'Card {o.account}: {o.number}'.format(o=self)


class Purchase(UUIDModel, TimeStampedModel):
    # account is None for cash payments
    account = models.ForeignKey(Account, related_name='purchases',
                                null=True, blank=True)
    status = EnumIntegerField(enums.PurchaseStatus,
                              default=enums.PurchaseStatus.FINALIZED)
    amount = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY
    )

    class Meta:
        ordering = ['-date_created']

    @property
    def deletable(self):
        max_delta = settings.PURCHASE_CANCEL_MAX_DELTA
        return timezone.now() - self.date_created <= max_delta

    def payment_method(self):
        return _('Cash') if self.account is None else _('FooCard')

    def __str__(self):
        return str(self.id)


class PurchaseItem(UUIDModel):
    purchase = models.ForeignKey(Purchase, related_name='items')
    product_id = models.UUIDField()
    qty = models.IntegerField(default=0)
    amount = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY
    )

    @property
    def product(self):
        return product_api.get_product(self.product_id)

    @property
    def total(self):
        return self.amount * self.qty

    def __str__(self):
        return str(self.id)


class WalletLogEntry(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(User, null=True, blank=True)
    trx_type = EnumIntegerField(enums.TrxType,
                                default=enums.TrxType.CORRECTION)
    wallet = models.ForeignKey('wallet.Wallet',
                               related_name='log_entries',
                               editable=False)
    comment = models.CharField(null=True, blank=True, max_length=128)
    amount = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY
    )
    pre_balance = MoneyField(
        verbose_name=_('old balance'),
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY
    )

    class Meta:
        verbose_name = _('wallet log entry')
        verbose_name_plural = _('wallet log entries')

    @property
    def post_balance(self):
        return self.pre_balance + self.amount

    def __str__(self):
        return str(self.id)
