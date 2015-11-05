from django.test import TestCase
from django.conf import settings
from foobar import api
from foobar.wallet import api as wallet_api
from shop.tests.factories import ProductFactory
from wallet.tests.factories import WalletFactory, WalletTrxFactory
from wallet.enums import TrxStatus
from .factories import AccountFactory
from moneyed import Money


class FoobarAPITest(TestCase):

    def test_get_account(self):
        obj1 = api.get_account(card_id=1337)
        self.assertIsNotNone(obj1)
        obj2 = api.get_account(card_id=1337)
        self.assertIsNotNone(obj2)
        self.assertEqual(obj1.id, obj2.id)
        obj3 = api.get_account(card_id=7331)
        self.assertIsNotNone(obj3)
        self.assertNotEqual(obj1.id, obj3.id)

    def test_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK'),
            trx_status=TrxStatus.FINALIZED
        )
        product_obj1 = ProductFactory.create(
            code='1337733113370',
            name='Billys Original',
            price=Money(13, 'SEK')
        )
        product_obj2 = ProductFactory.create(
            code='7331733113370',
            name='Kebaba',
            price=Money(30, 'SEK')
        )
        products = [
            (product_obj1.id, 3),
            (product_obj2.id, 1),
        ]
        api.purchase(account_obj.id, products)
        product_obj1.refresh_from_db()
        product_obj2.refresh_from_db()
        self.assertEqual(product_obj1.qty, -3)
        self.assertEqual(product_obj2.qty, -1)
        _, balance = wallet_api.get_balance(account_obj.id)
        self.assertEqual(balance, Money(931, 'SEK'))
        _, balance = wallet_api.get_balance(settings.FOOBAR_MAIN_WALLET)
        self.assertEqual(balance, Money(69, 'SEK'))

    def test_cash_purchase(self):
        product_obj1 = ProductFactory.create(
            code='1337733113370',
            name='Billys Original',
            price=Money(13, 'SEK')
        )
        product_obj2 = ProductFactory.create(
            code='7331733113370',
            name='Kebaba',
            price=Money(30, 'SEK')
        )
        products = [
            (product_obj1.id, 3),
            (product_obj2.id, 1),
        ]
        api.purchase(None, products)
        product_obj1.refresh_from_db()
        product_obj2.refresh_from_db()
        self.assertEqual(product_obj1.qty, -3)
        self.assertEqual(product_obj2.qty, -1)
        _, balance = wallet_api.get_balance(settings.FOOBAR_CASH_WALLET)
        self.assertEqual(balance, Money(69, 'SEK'))
