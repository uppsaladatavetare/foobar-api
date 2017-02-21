import random

import factory.fuzzy
from .. import models


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account


class CardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Card

    account = factory.SubFactory(AccountFactory)

    @factory.lazy_attribute
    def number(self):
        value = random.randint(0, (1 << 32) - 1)
        return str(value)
