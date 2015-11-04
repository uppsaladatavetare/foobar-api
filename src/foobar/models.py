from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from djmoney.models.fields import MoneyField
from bananas.models import UUIDModel, TimeStampedModel
from moneyed import Money


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
    account = models.ForeignKey(Account)

    @property
    def amount(self):
        qs = self.items.all()
        zero_money = Money(0, settings.DEFAULT_CURRENCY)
        return sum((item.amount * item.qty for item in qs), zero_money)

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

    def __str__(self):
        return str(self.id)
