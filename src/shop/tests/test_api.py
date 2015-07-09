from django.test import TestCase
from .. import api, models, enums
from . import factories


class ShopAPITest(TestCase):
    def test_create_product(self):
        product_obj = api.create_product(code='1234567812345', name='Banana')
        self.assertIsNotNone(product_obj)
        self.assertEqual(product_obj.code, '1234567812345')
        self.assertEqual(product_obj.name, 'Banana')
        self.assertEqual(product_obj.qty, 0)
        self.assertEqual(models.Product.objects.count(), 1)

    def test_get_product(self):
        product_obj1 = api.create_product(code='1234567812345', name='Banana')
        product_obj2 = api.get_product(product_obj1.id)
        self.assertIsNotNone(product_obj2)
        self.assertEqual(product_obj1.id, product_obj2.id)

    def test_create_product_transaction(self):
        product_obj = api.create_product(code='1234567812345', name='Banana')
        trx_obj = api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=enums.TrxType.INVENTORY,
            qty=1
        )
        self.assertIsNotNone(trx_obj)
        product_obj = api.get_product(product_obj.id)
        self.assertEqual(product_obj.qty, 1)
        trx_obj = api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=enums.TrxType.PURCHASE,
            qty=-2
        )
        self.assertIsNotNone(trx_obj)
        product_obj = api.get_product(product_obj.id)
        self.assertEqual(product_obj.qty, -1)

    def test_list_products(self):
        for _ in range(14):
            factories.ProductFactory.create()
        factories.ProductFactory.create(
            code='1337733113370',
            name='Billys Original'
        )
        self.assertEqual(len(api.list_products()), 15)
        self.assertEqual(len(api.list_products(limit=5)), 5)
        self.assertEqual(len(api.list_products(start=10)), 5)
        self.assertEqual(len(api.list_products(active=False)), 0)
        self.assertEqual(len(api.list_products(active=False)), 0)
        objs = api.list_products(name__startswith='Billys')
        self.assertEqual(len(objs), 1)
