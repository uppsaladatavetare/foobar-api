import factory.fuzzy
from .. import models, enums
from moneyed import Money


class FuzzyMoney(factory.fuzzy.FuzzyDecimal):
    def fuzz(self):
        return Money(super().fuzz(), 'SEK')


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Product

    name = factory.Sequence(lambda n: 'Product #{0}'.format(n))
    code = factory.Sequence(lambda n: '1{0:012d}'.format(n))
    price = FuzzyMoney(0, 100000)
    active = True


class ProductTrxFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductTransaction

    product = factory.SubFactory(ProductFactory)
    qty = factory.fuzzy.FuzzyInteger(-10, -1)
    trx_type = enums.TrxType.PURCHASE


class ProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductCategory

    name = factory.Sequence(lambda n: 'Category #{0}'.format(n))
