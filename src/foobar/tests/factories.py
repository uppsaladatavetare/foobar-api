import uuid
import factory.fuzzy
from .. import models
from utils.factories import FuzzyMoney


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account


class CardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Card

    account = factory.SubFactory(AccountFactory)
    number = factory.fuzzy.FuzzyInteger(0, (1 << 32) - 1)


class PurchaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Purchase

    account = factory.SubFactory(AccountFactory)
    amount = factory.fuzzy.FuzzyInteger(0, 1337)


class PurchaseItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PurchaseItem

    purchase = factory.SubFactory(PurchaseFactory)
    product_id = factory.fuzzy.FuzzyAttribute(uuid.uuid4)
    qty = 1
    amount = FuzzyMoney(0, 1000)


class PurchaseStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PurchaseStatus

    purchase = factory.SubFactory(PurchaseFactory)
