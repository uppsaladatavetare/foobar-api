from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils import timezone
from enumfields import EnumIntegerField
from djmoney.models.fields import MoneyField
from bananas.models import UUIDModel, TimeStampedModel
from moneyed import Money
from shop import api as product_api
from . import enums


class Account(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(User, null=True, blank=True)
    name = models.CharField(null=True, blank=True, max_length=128)
    email = models.CharField(null=True, blank=True, max_length=128)

    # The card id is a uid from a mifare classic 1k card and is supposed
    # to be 8 bytes long.
    card_id = models.CharField(unique=True, max_length=20)

    def clean(self):
        try:
            int(self.card_id)
        except ValueError:
            raise ValidationError(_('The card id should be an integer.'))

    def __str__(self):
        return str(self.id)


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
