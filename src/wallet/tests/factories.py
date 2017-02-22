import uuid
import factory.fuzzy
from .. import models, enums
from moneyed import Money


class FuzzyMoney(factory.fuzzy.FuzzyDecimal):
    def fuzz(self):
        return Money(super().fuzz(), 'SEK')


class WalletFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Wallet

    owner_id = factory.Sequence(lambda n: str(uuid.uuid4()))
    balance = Money(0, 'SEK')


class WalletTrxFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.WalletTransaction

    wallet = factory.SubFactory(WalletFactory)
    amount = FuzzyMoney(0, 100000)
    trx_type = enums.TrxType.FINALIZED
