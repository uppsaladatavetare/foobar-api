import uuid
import factory.fuzzy

from django.conf import settings
from .. import models
from utils.factories import FuzzyMoney


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    username = factory.Sequence('terminator{0}'.format)
    email = factory.Sequence('terminator{0}@skynet.com'.format)
    password = 'hunter2'
    is_superuser = False
    is_staff = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Account

    user = factory.SubFactory(UserFactory)


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
