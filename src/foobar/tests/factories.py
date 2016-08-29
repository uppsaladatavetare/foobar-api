import factory.fuzzy
from .. import models


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account


class CardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Card

    account = factory.SubFactory(AccountFactory)
    number = factory.fuzzy.FuzzyInteger(0, (1 << 32) - 1)
