from unittest import mock
from decimal import Decimal

from moneyed import Money

from django.test import TestCase
from django.contrib.auth.models import User

from ..suppliers.base import SupplierBase, DeliveryItem, SupplierProduct
from .. import api, models, enums, exceptions
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
            price='9',
            qty_multiplier=2
        )
        delivery_obj = factories.DeliveryFactory(
            supplier=supplier_obj,
            report='dummy'
        )
        delivery_obj = api.populate_delivery(delivery_obj.id)
        self.assertIsNotNone(delivery_obj)
        delivery_obj.refresh_from_db()
        delivery_items = delivery_obj.delivery_items.all()
        self.assertEqual(len(delivery_items), 1)
        # The quantity and the price should be recalculated
        # according to the multiplier.
        self.assertEqual(delivery_items[0].qty, 40)
        self.assertEqual(delivery_items[0].price.amount, Decimal('4.62'))

    def test_process_delivery(self):
        delivery_obj = factories.DeliveryFactory()
        item_obj1 = factories.DeliveryItemFactory(
            delivery=delivery_obj,
            qty=10,
            price=Money(50, 'SEK'),
            received=True

        )
        self.assertTrue(item_obj1.is_associated)
        product_obj1 = item_obj1.supplier_product.product
        pre_qty1 = product_obj1.qty
        item_obj2 = factories.DeliveryItemFactory(
            delivery=delivery_obj,
            qty=5,
            price=Money(10, 'SEK'),
            received=False
        )
        self.assertTrue(item_obj2.is_associated)
        product_obj2 = item_obj2.supplier_product.product
        pre_qty2 = product_obj2.qty
        self.assertFalse(delivery_obj.valid)
        item_obj2.received = True
        item_obj2.save()
        self.assertTrue(delivery_obj.valid)
        api.process_delivery(delivery_obj.id)
        trxs_qs = models.ProductTransaction.objects
        self.assertEqual(trxs_qs.count(), 2)
        product_obj1.refresh_from_db()
        product_obj2.refresh_from_db()
        self.assertEqual(product_obj1.qty - pre_qty1, 10)
        self.assertEqual(product_obj2.qty - pre_qty2, 5)

    def test_initiate_stockchecking(self):
        factories.ProductFactory.create_batch(size=3)
        stocktake_obj = api.initiate_stocktaking(chunk_size=2)
        self.assertIsNotNone(stocktake_obj)
        stocktake_qs = models.Stocktake.objects
        self.assertEqual(stocktake_qs.count(), 1)
        chunk_qs = stocktake_obj.chunks
        self.assertEqual(chunk_qs.count(), 2)
        chunk_objs = chunk_qs.all()
        self.assertEqual(chunk_objs[0].items.count(), 2)
        self.assertEqual(chunk_objs[1].items.count(), 1)
        product_ids = [
            chunk_objs[0].items.all()[0].id,
            chunk_objs[0].items.all()[1].id,
            chunk_objs[1].items.all()[0].id
        ]
        self.assertEqual(len(set(product_ids)), 3)
        # Make sure that only one stocktaking can place at the same time
        with self.assertRaises(exceptions.APIException):
            api.initiate_stocktaking()

    def test_finalize_stocktaking(self):
        stocktake_obj = factories.StocktakeFactory.create()
        chunk_obj1 = factories.StocktakeChunkFactory.create(
            stocktake=stocktake_obj,
            locked=True
        )
        chunk_obj2 = factories.StocktakeChunkFactory.create(
            stocktake=stocktake_obj,
            locked=False
        )
        product_obj1 = factories.ProductFactory.create()
        product_obj2 = factories.ProductFactory.create()
        product_obj3 = factories.ProductFactory.create()
        factories.ProductTrxFactory(product=product_obj1, qty=-100)
        factories.ProductTrxFactory(product=product_obj2, qty=0)
        factories.ProductTrxFactory(product=product_obj3, qty=50)
        item1 = factories.StocktakeItemFactory.create(
            product=product_obj1,
            chunk=chunk_obj1,
            qty=5
        )
        item2 = factories.StocktakeItemFactory.create(
            product=product_obj2,
            chunk=chunk_obj1,
            qty=1
        )
        item3 = factories.StocktakeItemFactory.create(
            product=product_obj3,
            chunk=chunk_obj2,
            qty=10
        )
        self.assertFalse(stocktake_obj.complete)
        with self.assertRaises(exceptions.APIException):
            api.finalize_stocktaking(stocktake_obj.id)
        chunk_obj2.locked = True
        chunk_obj2.save()
        self.assertTrue(stocktake_obj.complete)
        api.finalize_stocktaking(stocktake_obj.id)
        item1.product.refresh_from_db()
        item2.product.refresh_from_db()
        item3.product.refresh_from_db()
        self.assertEqual(item1.product.qty, 5)
        self.assertEqual(item2.product.qty, 1)
        self.assertEqual(item3.product.qty, 10)
        stocktake_obj.refresh_from_db()
        self.assertTrue(stocktake_obj.locked)
        trxs_qs = models.ProductTransaction.objects
        self.assertEqual(trxs_qs.count(), 6)

    def test_finalize_stocktake_chunk(self):
        stocktake_obj = factories.StocktakeFactory.create()
        chunk_obj1 = factories.StocktakeChunkFactory.create(
            stocktake=stocktake_obj,
            locked=False
        )
        api.finalize_stocktake_chunk(chunk_obj1.id)
        chunk_obj1.refresh_from_db()
        self.assertTrue(chunk_obj1.locked)

    def test_assign_free_stocktake_chunk(self):
        stocktake_obj = factories.StocktakeFactory.create()
        factories.StocktakeChunkFactory.create(
            stocktake=stocktake_obj,
            locked=False
        )
        factories.StocktakeChunkFactory.create(
            stocktake=stocktake_obj,
            locked=True
        )
        factories.StocktakeChunkFactory.create(
            stocktake=stocktake_obj,
            locked=False
        )
        user_obj = User.objects.create_superuser(
            'the_baconator', 'bacon@foobar.com', '123'
        )
        obj1 = api.assign_free_stocktake_chunk(user_obj.id, stocktake_obj.id)
        self.assertIsNotNone(obj1)
        # Work on the first chunk not yet completed
        obj2 = api.assign_free_stocktake_chunk(user_obj.id, stocktake_obj.id)
        self.assertIsNotNone(obj1)
        self.assertEqual(obj1.id, obj2.id)
        api.finalize_stocktake_chunk(obj1.id)
        # Work on the next chunk
        obj3 = api.assign_free_stocktake_chunk(user_obj.id, stocktake_obj.id)
        self.assertIsNotNone(obj3)
        self.assertNotEqual(obj2.id, obj3.id)
        api.finalize_stocktake_chunk(obj3.id)
        # Work is finished
        obj4 = api.assign_free_stocktake_chunk(user_obj.id, stocktake_obj.id)
        self.assertIsNone(obj4)
