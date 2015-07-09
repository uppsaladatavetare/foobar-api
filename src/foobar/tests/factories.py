import factory.fuzzy
from .. import models


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account

    card_id = factory.fuzzy.FuzzyInteger(0, (1 << 32) - 1)
