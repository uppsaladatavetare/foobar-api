import uuid
import factory.fuzzy
from .. import models, enums
from moneyed import Money
from utils.factories import FuzzyMoney


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


class WalletTrxStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.WalletTransactionStatus

    trx = factory.SubFactory(WalletTrxFactory)
    status = enums.TrxStatus.FINALIZED


class WalletTrxWithStatusFactory(WalletTrxFactory):
    states = factory.RelatedFactory(
        WalletTrxStatusFactory,
        'trx',
        status=enums.TrxStatus.FINALIZED
    )
