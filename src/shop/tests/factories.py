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
    price = FuzzyMoney(10, 50)
    active = True


class ProductTrxFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductTransaction

    product = factory.SubFactory(ProductFactory)
    qty = 0
    trx_type = enums.TrxType.PURCHASE


class ProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductCategory

    name = factory.Sequence(lambda n: 'Category #{0}'.format(n))


class SupplierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Supplier


class SupplierProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SupplierProduct

    supplier = factory.SubFactory(SupplierFactory)
    product = factory.SubFactory(ProductFactory)
    name = factory.Sequence(lambda n: 'Product #{0}'.format(n))
    sku = factory.Sequence(lambda n: '1{0:010d}'.format(n))
    price = FuzzyMoney(10, 50)


class DeliveryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Delivery

    supplier = factory.SubFactory(SupplierFactory)
    report = 'dummy'


class DeliveryItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DeliveryItem

    delivery = factory.SubFactory(SupplierFactory)
    supplier_product = factory.SubFactory(SupplierProductFactory)
    qty = factory.fuzzy.FuzzyInteger(1, 50)
    price = FuzzyMoney(10, 50)
    received = True


class StocktakeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Stocktake


class StocktakeChunkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.StocktakeChunk

    stocktake = factory.SubFactory(StocktakeFactory)


class StocktakeItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.StocktakeItem

    chunk = factory.SubFactory(StocktakeChunkFactory)
    product = factory.SubFactory(ProductFactory)
    qty = factory.fuzzy.FuzzyInteger(1, 50)
