from django.test import TestCase
from django.conf import settings
from foobar import api, enums, models
from foobar.wallet import api as wallet_api
from shop.tests.factories import ProductFactory
from wallet.tests.factories import WalletFactory, WalletTrxFactory
from wallet.enums import TrxType
from .factories import AccountFactory, CardFactory
from moneyed import Money
from django.contrib.auth.models import User


class FoobarAPITest(TestCase):
    def test_get_card(self):
        # Retrieve an non-existent account
        obj1 = api.get_card(1337)
        self.assertIsNone(obj1)

        # Create an account
        CardFactory.create(number=1337)
        obj2 = api.get_card(1337)
        self.assertIsNotNone(obj2)
        self.assertIsNotNone(obj2.date_used)

        date_used = obj2.date_used
        obj2 = api.get_card(1337)
        self.assertGreater(obj2.date_used, date_used)

    def test_get_account(self):
        # Retrieve an non-existent account
        obj1 = api.get_account(card_id=1337)
        self.assertIsNone(obj1)

        # Create an account
        CardFactory.create(number=1337)
        obj2 = api.get_account(card_id=1337)

        self.assertIsNotNone(obj2)

        account_objs = models.Account.objects.filter(id=obj2.id)
        self.assertEqual(account_objs.count(), 1)

    def test_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK'),
            trx_type=TrxType.FINALIZED
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
        purchase_obj = api.purchase(account_obj.id, products)
        self.assertEqual(purchase_obj.amount, Money(69, 'SEK'))
        product_obj1.refresh_from_db()
        product_obj2.refresh_from_db()
        self.assertEqual(product_obj1.qty, -3)
        self.assertEqual(product_obj2.qty, -1)
        _, balance = wallet_api.get_balance(account_obj.id)
        self.assertEqual(balance, Money(931, 'SEK'))
        _, balance = wallet_api.get_balance(settings.FOOBAR_MAIN_WALLET)
        self.assertEqual(balance, Money(69, 'SEK'))

    def test_cancel_card_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK'),
            trx_type=TrxType.FINALIZED
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
        purchase_obj = api.purchase(account_obj.id, products)
        api.cancel_purchase(purchase_obj.id)
        purchase_obj, _ = api.get_purchase(purchase_obj.id)
        self.assertEqual(purchase_obj.status, enums.PurchaseStatus.CANCELED)
        product_obj1.refresh_from_db()
        product_obj2.refresh_from_db()
        self.assertEqual(product_obj1.qty, 0)
        self.assertEqual(product_obj2.qty, 0)
        _, balance = wallet_api.get_balance(account_obj.id)
        self.assertEqual(balance, Money(1000, 'SEK'))
        _, balance = wallet_api.get_balance(settings.FOOBAR_MAIN_WALLET)
        self.assertEqual(balance, Money(0, 'SEK'))

    def test_cancel_cash_purchase(self):
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
        purchase_obj = api.purchase(None, products)
        api.cancel_purchase(purchase_obj.id)
        purchase_obj, _ = api.get_purchase(purchase_obj.id)
        self.assertEqual(purchase_obj.status, enums.PurchaseStatus.CANCELED)
        product_obj1.refresh_from_db()
        product_obj2.refresh_from_db()
        self.assertEqual(product_obj1.qty, 0)
        self.assertEqual(product_obj2.qty, 0)
        _, balance = wallet_api.get_balance(settings.FOOBAR_CASH_WALLET)
        self.assertEqual(balance, Money(0, 'SEK'))

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

    def test_get_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK'),
            trx_type=TrxType.FINALIZED
        )
        product_obj1 = ProductFactory.create(
            code='1337733113370',
            name='Billys Original',
            price=Money(13, 'SEK')
        )
        products = [
            (product_obj1.id, 3),
        ]
        purchase_obj = api.purchase(account_obj.id, products)
        obj = api.get_purchase(purchase_obj.id)
        self.assertIsNotNone(obj)

    def test_list_purchases(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK'),
            trx_type=TrxType.FINALIZED
        )
        product_obj1 = ProductFactory.create(
            code='1337733113370',
            name='Billys Original',
            price=Money(13, 'SEK')
        )
        products = [
            (product_obj1.id, 3),
        ]
        api.purchase(account_obj.id, products)
        objs = api.list_purchases(account_obj.id)
        self.assertEqual(len(objs), 1)

    def test_calculation_correctíon(self):
        wallet_obj = WalletFactory.create()
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK'),
            trx_type=TrxType.FINALIZED
        )
        user_obj = User.objects.create_superuser(
            'the_baconator', 'bacon@foobar.com', '123'
        )
        # Test positive balance change
        correction_obj = api.calculate_correction(
            new_balance=Money(1200, 'SEK'),
            user=user_obj,
            owner_id=wallet_obj.owner_id
        )
        self.assertEqual(correction_obj.wallet.owner_id, wallet_obj.owner_id)
        self.assertEqual(correction_obj.trx_type.value, 0)
        self.assertEqual(correction_obj.pre_balance.amount, 1000)
        self.assertEqual(correction_obj.amount.amount, 200)
        _, balance_correction = wallet_api.get_balance(
            correction_obj.wallet.owner_id
        )
        self.assertEqual(balance_correction.amount, 1200)
        # Test negative balance change
        correction_obj = api.calculate_correction(
            new_balance=Money(1000, 'SEK'),
            user=user_obj,
            owner_id=wallet_obj.owner_id
        )
        self.assertEqual(correction_obj.wallet.owner_id, wallet_obj.owner_id)
        self.assertEqual(correction_obj.trx_type.value, 0)
        self.assertEqual(correction_obj.pre_balance.amount, 1200)
        self.assertEqual(correction_obj.amount.amount, -200)
        _, balance_correction = wallet_api.get_balance(
            correction_obj.wallet.owner_id
        )
        self.assertEqual(balance_correction.amount, 1000)
        # Test when balance is the same = no change
        correction_obj = api.calculate_correction(
            new_balance=Money(1000, 'SEK'),
            user=user_obj,
            owner_id=wallet_obj.owner_id
        )
        self.assertEqual(correction_obj.wallet.owner_id, wallet_obj.owner_id)
        self.assertEqual(correction_obj.trx_type.value, 0)
        self.assertEqual(correction_obj.pre_balance.amount, 1000)
        self.assertEqual(correction_obj.amount.amount, 0)
        _, balance_correction = wallet_api.get_balance(
            correction_obj.wallet.owner_id
        )
        self.assertEqual(balance_correction.amount, 1000)

    def test_make_deposit_or_withdrawal(self):
        wallet_obj = WalletFactory.create()
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK'),
            trx_type=TrxType.FINALIZED
        )
        user_obj = User.objects.create_superuser(
            'the_baconator', 'bacon@foobar.com', '123'
        )
        # Test a deposit
        correction_obj = api.make_deposit_or_withdrawal(
            amount=Money(100, 'SEK'),
            user=user_obj,
            owner_id=wallet_obj.owner_id
         )
        self.assertEqual(correction_obj.wallet.owner_id, wallet_obj.owner_id)
        self.assertEqual(correction_obj.trx_type, enums.TrxType.DEPOSIT)
        self.assertEqual(correction_obj.pre_balance.amount, 1000)
        self.assertEqual(correction_obj.amount.amount, 100)
        _, balance = wallet_api.get_balance(wallet_obj.owner_id)
        self.assertEqual(balance.amount, 1100)
        # Test a withdraw
        correction_obj = api.make_deposit_or_withdrawal(
            amount=Money(-50, 'SEK'),
            user=user_obj, owner_id=wallet_obj.owner_id
        )
        self.assertEqual(correction_obj.wallet.owner_id, wallet_obj.owner_id)
        self.assertEqual(correction_obj.trx_type, enums.TrxType.WITHDRAWAL)
        self.assertEqual(correction_obj.pre_balance.amount, 1100)
        self.assertEqual(correction_obj.amount.amount, -50)
        _, balance = wallet_api.get_balance(wallet_obj.owner_id)
        self.assertEqual(balance.amount, 1050)
        # Test when user tries to deposit or withdraw 0
        correction_obj = api.make_deposit_or_withdrawal(
            amount=Money(0, 'SEK'),
            user=user_obj,
            owner_id=wallet_obj.owner_id
        )
        self.assertEqual(correction_obj.wallet.owner_id, wallet_obj.owner_id)
        self.assertEqual(correction_obj.trx_type, enums.TrxType.CORRECTION)
        self.assertEqual(correction_obj.pre_balance.amount, 1050)
        self.assertEqual(correction_obj.amount.amount, 0)
        _, balance = wallet_api.get_balance(wallet_obj.owner_id)
        self.assertEqual(balance.amount, 1050)
