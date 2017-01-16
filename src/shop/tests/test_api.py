from unittest import mock
from decimal import Decimal

from moneyed import Money

from django.test import TestCase

from ..suppliers.base import SupplierBase, DeliveryItem, SupplierProduct
from .. import api, models, enums
from .models import DummyModel
from . import factories


class DummySupplierAPI(SupplierBase):
    def parse_delivery_report(self, report_path):
        return [
            DeliveryItem(
                sku='101176931',
                qty=20,
                price=Decimal('9.25')
            )
        ]

    def retrieve_product(self, sku):
        return SupplierProduct(
            name='Billys Original',
            price=Decimal('9.25')
        )


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

    def test_get_product_transactions_by_ref(self):
        dummy_obj = DummyModel.objects.create()
        product_obj = factories.ProductFactory.create()
        api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=enums.TrxType.INVENTORY,
            qty=1,
            reference=dummy_obj
        )
        api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=enums.TrxType.INVENTORY,
            qty=1,
            reference=dummy_obj
        )
        trx_objs = api.get_product_transactions_by_ref(dummy_obj)
        self.assertEqual(len(trx_objs), 2)

    def test_cancel_product_transaction(self):
        product_obj = factories.ProductFactory.create()
        trx_obj = api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=enums.TrxType.INVENTORY,
            qty=1
        )
        trx_obj = api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=enums.TrxType.INVENTORY,
            qty=2
        )
        product_obj = api.get_product(product_obj.id)
        self.assertEqual(product_obj.qty, 3)
        api.cancel_product_transaction(trx_obj.id)
        product_obj = api.get_product(product_obj.id)
        self.assertEqual(product_obj.qty, 1)

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

    @mock.patch('shop.suppliers.get_supplier_api')
    def test_get_supplier_product_existing(self, mock_get_supplier_api):
        mock_get_supplier_api.return_value = DummySupplierAPI()
        supplier_obj = factories.SupplierFactory.create()
        factories.SupplierProductFactory.create(
            supplier=supplier_obj,
            name='Billys',
            sku='101176931',
            price=1337
        )
        product_obj = api.get_supplier_product(supplier_obj.id, '101176931')
        self.assertIsNotNone(product_obj)
        self.assertEqual(product_obj.sku, '101176931')
        self.assertEqual(product_obj.price.amount, 1337)

    @mock.patch('shop.suppliers.get_supplier_api')
    def test_get_supplier_product_non_existing(self, mock_get_supplier_api):
        mock_get_supplier_api.return_value = DummySupplierAPI()
        supplier_obj = factories.SupplierFactory.create()
        product_obj = api.get_supplier_product(supplier_obj.id, '101176931')
        self.assertIsNotNone(product_obj)
        self.assertEqual(product_obj.sku, '101176931')
        self.assertEqual(product_obj.price.amount, Decimal('9.25'))

    @mock.patch('shop.suppliers.get_supplier_api')
    def test_populate_delivery(self, mock_get_supplier_api):
        mock_get_supplier_api.return_value = DummySupplierAPI()
        supplier_obj = factories.SupplierFactory.create()
        factories.SupplierProductFactory.create(
            supplier=supplier_obj,
            name='Billys',
            sku='101176931',
            price='9'
        )
        delivery_obj = factories.DeliveryFactory(
            supplier=supplier_obj,
            report='dummy'
        )
        delivery_obj = api.populate_delivery(delivery_obj.id)
        self.assertIsNotNone(delivery_obj)
        delivery_objs = models.Delivery.objects.all()
        self.assertEqual(len(delivery_objs), 1)
        delivery_obj = delivery_objs[0]
        delivery_items = delivery_obj.items.all()
        self.assertEqual(len(delivery_items), 1)

    def test_process_delivery(self):
        delivery_obj = factories.DeliveryFactory()
        item_obj1 = factories.DeliveryItemFactory(
            delivery=delivery_obj,
            qty=10,
            price=Money(50, 'SEK')
        )
        self.assertTrue(item_obj1.is_associated)
        product_obj1 = item_obj1.supplier_product.product
        pre_qty1 = product_obj1.qty
        item_obj2 = factories.DeliveryItemFactory(
            delivery=delivery_obj,
            qty=5,
            price=Money(10, 'SEK')
        )
        self.assertTrue(item_obj2.is_associated)
        product_obj2 = item_obj2.supplier_product.product
        pre_qty2 = product_obj2.qty
        api.process_delivery(delivery_obj.id)
        trxs_qs = models.ProductTransaction.objects
        self.assertEqual(trxs_qs.count(), 2)
        product_obj1.refresh_from_db()
        product_obj2.refresh_from_db()
        self.assertEqual(product_obj1.qty - pre_qty1, 10)
        self.assertEqual(product_obj2.qty - pre_qty2, 5)
