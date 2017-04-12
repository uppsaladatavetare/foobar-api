from datetime import date, datetime
from decimal import Decimal
from unittest import mock

from moneyed import Money

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from ..suppliers.base import (
    DeliveryItem,
    SupplierAPIException,
    SupplierProduct
)
from .. import api, models, enums, exceptions
from .models import DummyModel
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
        self.assertEqual(trx_obj.trx_status, enums.TrxStatus.PENDING)

        product_obj = api.get_product(product_obj.id)
        self.assertEqual(product_obj.qty, 1)
        trx_obj = api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=enums.TrxType.PURCHASE,
            qty=-2
        )
        self.assertIsNotNone(trx_obj)
        self.assertEqual(trx_obj.trx_status, enums.TrxStatus.PENDING)

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

        trx_obj.refresh_from_db()
        self.assertEqual(trx_obj.trx_status, enums.TrxStatus.CANCELED)

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

    def test_get_supplier_product_existing(self):
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
        m = mock_get_supplier_api.return_value = mock.MagicMock()
        m.retrieve_product.return_value = SupplierProduct(
            name='Billys Original',
            price=Decimal('9.25'),
            units=1
        )
        supplier_obj = factories.SupplierFactory.create()
        product_obj = api.get_supplier_product(supplier_obj.id, '101176931')
        self.assertIsNotNone(product_obj)
        self.assertEqual(product_obj.sku, '101176931')
        self.assertEqual(product_obj.price.amount, Decimal('9.25'))

    @mock.patch('shop.suppliers.get_supplier_api')
    def test_populate_delivery(self, mock_get_supplier_api):
        m = mock_get_supplier_api.return_value = mock.MagicMock()
        m.parse_delivery_report.return_value = [
            DeliveryItem(
                sku='101176931',
                qty=20,
                price=Decimal('9.25')
            )
        ]
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
        factories.StocktakeChunkFactory.create(
            stocktake=stocktake_obj,
            locked=False
        )
        user_obj1 = User.objects.create_superuser(
            'the_baconator', 'bacon@foobar.com', '123'
        )
        user_obj2 = User.objects.create_superuser(
            'ludo', 'ludo@foobar.com', '123'
        )
        obj1 = api.assign_free_stocktake_chunk(user_obj1.id, stocktake_obj.id)
        self.assertIsNotNone(obj1)
        # Work on the first chunk not yet completed
        obj2 = api.assign_free_stocktake_chunk(user_obj1.id, stocktake_obj.id)
        self.assertIsNotNone(obj1)
        self.assertEqual(obj1.id, obj2.id)
        api.finalize_stocktake_chunk(obj1.id)
        # Work on the next chunk
        obj3 = api.assign_free_stocktake_chunk(user_obj1.id, stocktake_obj.id)
        self.assertIsNotNone(obj3)
        self.assertNotEqual(obj2.id, obj3.id)
        # Another user wants to work too
        obj4 = api.assign_free_stocktake_chunk(user_obj2.id, stocktake_obj.id)
        self.assertIsNotNone(obj4)
        self.assertNotEqual(obj3.id, obj4.id)
        api.finalize_stocktake_chunk(obj3.id)
        api.finalize_stocktake_chunk(obj4.id)
        # Work is finished
        obj5 = api.assign_free_stocktake_chunk(user_obj1.id, stocktake_obj.id)
        self.assertIsNone(obj5)

    def test_predict_quantity(self):
        initial_qty = 100
        initial_timestamp = datetime(2016, 11, 14, 0)
        trx_data = [
            (-5,  datetime(2016, 11, 15, 0)),
            (-10, datetime(2016, 11, 16, 0)),
            (-5,  datetime(2016, 11, 18, 0)),
            (-5,  datetime(2016, 11, 18, 1)),
        ]
        product = factories.ProductFactory.create()
        # No product transactions yet
        timestamp = api.predict_quantity(product.id, product.qty - 1,
                                         current_date=date(2016, 11, 18))
        self.assertIsNone(timestamp)
        trx_obj = factories.ProductTrxFactory.create(
            product=product,
            qty=initial_qty,
            trx_type=enums.TrxType.INVENTORY,
            date_created=timezone.make_aware(initial_timestamp)
        )
        factories.ProductTrxStatusFactory(
            trx=trx_obj,
            status=enums.TrxStatus.PENDING,
            date_created=timezone.make_aware(initial_timestamp)
        )
        factories.ProductTrxStatusFactory(
            trx=trx_obj,
            status=enums.TrxStatus.FINALIZED,
            date_created=timezone.make_aware(initial_timestamp)
        )
        # Product restocked, but no purchases made yet
        timestamp = api.predict_quantity(product.id, 0,
                                         current_date=date(2016, 11, 18))
        self.assertIsNone(timestamp)
        for qty, timestamp in trx_data:
            trx_obj = factories.ProductTrxFactory.create(
                product=product,
                qty=qty,
                date_created=timezone.make_aware(timestamp),
                trx_type=enums.TrxType.PURCHASE
            )
            factories.ProductTrxStatusFactory(
                trx=trx_obj,
                status=enums.TrxStatus.PENDING,
                date_created=timezone.make_aware(timestamp)
            )
            factories.ProductTrxStatusFactory(
                trx=trx_obj,
                status=enums.TrxStatus.FINALIZED,
                date_created=timezone.make_aware(timestamp)
            )
        timestamp = api.predict_quantity(product.id,
                                         target=product.qty,
                                         current_date=date(2016, 11, 18))
        self.assertIsNone(timestamp)
        timestamp = api.predict_quantity(product.id, 0,
                                         current_date=date(2016, 11, 18))
        self.assertEqual(timestamp, date(2016, 11, 30))

    def test_predict_quantity_non_decreasing_function(self):
        initial_qty = 100
        initial_timestamp = datetime(2016, 11, 14, 0)
        trx_data = [
            (-5,  datetime(2016, 11, 15, 0)),
            (+5,  datetime(2016, 11, 15, 0)),
        ]
        product = factories.ProductFactory.create()
        factories.ProductTrxFactory.create(
            product=product,
            qty=initial_qty,
            trx_type=enums.TrxType.INVENTORY,
            date_created=timezone.make_aware(initial_timestamp)
        )
        for qty, timestamp in trx_data:
            factories.ProductTrxFactory.create(
                product=product,
                qty=qty,
                date_created=timezone.make_aware(timestamp),
                trx_type=enums.TrxType.PURCHASE
            )
        # Product restocked, but no purchases made yet
        timestamp = api.predict_quantity(product.id, 0)
        self.assertIsNone(timestamp)

    @mock.patch('shop.api.predict_quantity')
    def test_update_quantity_prediction(self, predict_quantity_mock):
        product = factories.ProductFactory.create()
        predict_quantity_mock.return_value = date(1337, 1, 1)
        api.update_out_of_stock_forecast(product.id)
        predict_quantity_mock.assert_called_once_with(product.id, target=0)
        product.refresh_from_db()
        self.assertEqual(product.out_of_stock_forecast, date(1337, 1, 1))

    @mock.patch('shop.suppliers.get_supplier_api')
    def test_order_from_supplier(self, mock_get_supplier_api):
        mock_supplier_api = mock.MagicMock()
        mock_get_supplier_api.return_value = mock_supplier_api
        mock_order_product = mock_supplier_api.order_product
        supplier1 = factories.SupplierFactory()
        supplier2 = factories.SupplierFactory()
        product1 = factories.ProductFactory()
        product2 = factories.ProductFactory()
        sp1 = factories.SupplierProductFactory(
            product=product1,
            supplier=supplier1,
            price=5,
            units=64
        )
        sp2 = factories.SupplierProductFactory(
            product=product1,
            supplier=supplier1,
            price=10,
            units=30
        )
        sp3 = factories.SupplierProductFactory(
            product=product1,
            supplier=supplier1,
            price=40,
            qty_multiplier=10,
            units=1
        )
        factories.SupplierProductFactory(
            product=product2,
            supplier=supplier2,
            price=1,
            units=1
        )
        sp5 = api.order_from_supplier(product1.id, 48)
        mock_order_product.assert_called_once_with(sp3.sku, 5)
        self.assertEqual(sp3.id, sp5.id)
        # Let's break the supplier API and see what happens.
        mock_order_product.reset_mock()
        mock_order_product.side_effect = SupplierAPIException
        with self.assertRaises(exceptions.APIException):
            api.order_from_supplier(product1.id, 48)
        mock_order_product.assert_has_calls([
            mock.call(sp3.sku, 5),
            mock.call(sp1.sku, 1),
            mock.call(sp2.sku, 2),
        ])

    @mock.patch('shop.api.order_from_supplier')
    def test_order_refill(self, mock_order_from_supplier):
        current_date = date(2017, 3, 2)
        product1 = factories.ProductFactory(
            qty=15,
            out_of_stock_forecast=date(2017, 3, 8)
        )
        product2 = factories.ProductFactory(
            qty=10,
            out_of_stock_forecast=date(2017, 3, 15)
        )
        factories.BaseStockLevel(product=product1, level=48)
        factories.BaseStockLevel(product=product2, level=32)
        supplier = factories.SupplierFactory(
            delivers_on=enums.Weekdays.WEDNESDAY.value
        )
        factories.SupplierProductFactory(
            supplier=supplier,
            product=product1
        )
        factories.SupplierProductFactory(
            supplier=supplier,
            product=product2
        )
        api.order_refill(supplier.id, current_date)
        mock_order_from_supplier.assert_has_calls([
            mock.call(product1.id, 48, supplier_id=supplier.id)
        ])

    def test_finalize_pending_product_trx(self):
        product_obj = factories.ProductFactory.create()
        trx_obj1 = api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=enums.TrxType.INVENTORY,
            qty=1
        )

        trx_obj2 = api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=enums.TrxType.INVENTORY,
            qty=2
        )
        product_obj.refresh_from_db()
        # We update quantity when a pending transaction is created
        self.assertEqual(product_obj.qty, 3)

        self.assertEqual(trx_obj1.trx_status, enums.TrxStatus.PENDING)
        self.assertEqual(trx_obj2.trx_status, enums.TrxStatus.PENDING)

        api.finalize_product_transaction(trx_obj1.pk)
        api.finalize_product_transaction(trx_obj2.pk)

        product_obj.refresh_from_db()
        self.assertEqual(trx_obj1.trx_status, enums.TrxStatus.FINALIZED)
        self.assertEqual(trx_obj2.trx_status, enums.TrxStatus.FINALIZED)
        # Quantity should not have changed when we've finalized
        self.assertEqual(product_obj.qty, 3)
