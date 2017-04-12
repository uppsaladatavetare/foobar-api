from unittest import mock
import uuid
from django.test import TestCase
from django.conf import settings
from foobar import api, enums, models
from foobar.wallet import api as wallet_api
from utils.exceptions import InvalidTransition
from shop.tests.factories import ProductFactory
from wallet.tests.factories import WalletFactory, WalletTrxFactory
from wallet import enums as wallet_enums
from .factories import AccountFactory, CardFactory, PurchaseItemFactory
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
        # Assure None when missing account
        id = uuid.uuid4()
        obj1 = api.get_account(account_id=id)
        self.assertIsNone(obj1)

        # Create an account
        account_obj = AccountFactory.create()
        obj2 = api.get_account(account_id=account_obj.id)
        obj3 = api.get_account(id=account_obj.id)
        self.assertEqual(obj2.id, obj3.id)

    def test_get_account_by_card(self):
        # Retrieve an non-existent account
        obj1 = api.get_account_by_card(card_id=1337)
        self.assertIsNone(obj1)

        # Create an account
        CardFactory.create(number=1337)
        obj2 = api.get_account_by_card(card_id=1337)

        self.assertIsNotNone(obj2)

        account_objs = models.Account.objects.filter(id=obj2.id)
        self.assertEqual(account_objs.count(), 1)

    def test_update_account(self):
        account_obj = AccountFactory.create()
        api.update_account(account_id=account_obj.id,
                           name='1337',
                           email='1337@foo.com')
        account = api.get_account(account_id=account_obj.id)
        # Test that correct fields are updated
        self.assertEqual('1337', account.name)
        self.assertEqual('1337@foo.com', account.email)

    def test_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(wallet_enums.TrxStatus.PENDING)
        trx_obj.set_status(wallet_enums.TrxStatus.FINALIZED)

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
        purchase_obj, _ = api.create_purchase(account_obj.id, products)
        self.assertEqual(purchase_obj.status, enums.PurchaseStatus.PENDING)
        self.assertEqual(purchase_obj.amount, Money(69, 'SEK'))

        product_obj1.refresh_from_db()
        product_obj2.refresh_from_db()
        self.assertEqual(product_obj1.qty, -3)
        self.assertEqual(product_obj2.qty, -1)

        _, balance = wallet_api.get_balance(account_obj.id)
        self.assertEqual(balance, Money(931, 'SEK'))
        _, balance = wallet_api.get_balance(settings.FOOBAR_MAIN_WALLET)
        self.assertEqual(balance, Money(0, 'SEK'))

        purchase_obj = api.finalize_purchase(purchase_obj.pk)
        self.assertEqual(purchase_obj.status, enums.PurchaseStatus.FINALIZED)
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
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(wallet_enums.TrxStatus.PENDING)
        trx_obj.set_status(wallet_enums.TrxStatus.FINALIZED)

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
        purchase_obj, _ = api.create_purchase(account_obj.id, products)
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
        purchase_obj, _ = api.create_purchase(None, products)
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
        purchase_obj, _ = api.create_purchase(account_id=None,
                                              products=products)
        self.assertEqual(purchase_obj.status, enums.PurchaseStatus.PENDING)
        product_obj1.refresh_from_db()
        product_obj2.refresh_from_db()
        self.assertEqual(product_obj1.qty, -3)
        self.assertEqual(product_obj2.qty, -1)
        _, balance = wallet_api.get_balance(settings.FOOBAR_CASH_WALLET)
        self.assertEqual(balance, Money(0, 'SEK'))

        purchase_obj = api.finalize_purchase(purchase_obj.pk)
        self.assertEqual(purchase_obj.status, enums.PurchaseStatus.FINALIZED)
        _, balance = wallet_api.get_balance(settings.FOOBAR_CASH_WALLET)
        self.assertEqual(balance, Money(69, 'SEK'))

    def test_get_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(wallet_enums.TrxStatus.PENDING)
        trx_obj.set_status(wallet_enums.TrxStatus.FINALIZED)

        product_obj1 = ProductFactory.create(
            code='1337733113370',
            name='Billys Original',
            price=Money(13, 'SEK')
        )
        products = [
            (product_obj1.id, 3),
        ]
        purchase_obj, _ = api.create_purchase(account_obj.id, products)
        obj, _ = api.get_purchase(purchase_obj.id)
        self.assertIsNotNone(obj)

    def test_list_purchases(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(wallet_enums.TrxStatus.PENDING)
        trx_obj.set_status(wallet_enums.TrxStatus.FINALIZED)

        product_obj1 = ProductFactory.create(
            code='1337733113370',
            name='Billys Original',
            price=Money(13, 'SEK')
        )
        products = [
            (product_obj1.id, 3),
        ]
        api.create_purchase(account_obj.id, products)
        objs = api.list_purchases(account_obj.id)
        self.assertEqual(len(objs), 1)

    def test_calculation_correction(self):
        wallet_obj = WalletFactory.create()
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(wallet_enums.TrxStatus.PENDING)
        trx_obj.set_status(wallet_enums.TrxStatus.FINALIZED)

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
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(wallet_enums.TrxStatus.PENDING)
        trx_obj.set_status(wallet_enums.TrxStatus.FINALIZED)

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

    def test_finalize_pending_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.pk)
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(wallet_enums.TrxStatus.PENDING)
        trx_obj.set_status(wallet_enums.TrxStatus.FINALIZED)

        product_obj1 = ProductFactory.create(
            code='8437438439393',
            name='Fat',
            price=Money(42, 'SEK')
        )
        products = [(product_obj1.pk, 3)]

        pending_obj, _ = api.create_purchase(
            account_id=account_obj.pk,
            products=products
        )

        self.assertIsNotNone(pending_obj.status)
        self.assertEqual(pending_obj.status, enums.PurchaseStatus.PENDING)
        self.assertEqual(pending_obj.states.count(), 1)
        self.assertEqual(pending_obj.account.pk, account_obj.pk)
        self.assertEqual(pending_obj.amount.amount, 126)

        _, balance = wallet_api.get_balance(wallet_obj.owner_id)
        self.assertEqual(balance, Money(874, 'SEK'))

        finalized_obj = api.finalize_purchase(purchase_id=pending_obj.pk)

        self.assertIsNotNone(finalized_obj.status)
        self.assertEqual(finalized_obj.status, enums.PurchaseStatus.FINALIZED)
        self.assertEqual(finalized_obj.states.count(), 2)
        self.assertEqual(finalized_obj.account.pk, account_obj.pk)
        self.assertEqual(finalized_obj.amount.amount, 126)

        _, balance = wallet_api.get_balance(wallet_obj.owner_id)
        self.assertEqual(balance, Money(874, 'SEK'))

        _, balance = wallet_api.get_balance(settings.FOOBAR_MAIN_WALLET)
        self.assertEqual(balance, Money(126, 'SEK'))

        self.assertEqual(finalized_obj.items.count(), 1)
        item = finalized_obj.items.first()

        self.assertEqual(item.qty, 3)
        self.assertEqual(item.amount.amount, 42)
        self.assertEqual(item.product_id, product_obj1.pk)

    @mock.patch('foobar.api.finalize_purchase')
    @mock.patch('foobar.api.cancel_purchase')
    def test_update_purchase_status(self, mock_cancel_purchase,
                                    mock_finalize_purchase):
        item1 = PurchaseItemFactory()
        purchase1 = item1.purchase
        api.update_purchase_status(purchase1.id,
                                   enums.PurchaseStatus.FINALIZED)
        mock_finalize_purchase.assert_called_once_with(purchase1.id)
        item2 = PurchaseItemFactory()
        purchase2 = item2.purchase
        api.update_purchase_status(purchase2.id,
                                   enums.PurchaseStatus.CANCELED)
        mock_cancel_purchase.assert_called_once_with(purchase2.id)
        item3 = PurchaseItemFactory()
        purchase3 = item3.purchase
        with self.assertRaises(InvalidTransition):
            api.update_purchase_status(purchase3.id,
                                       enums.PurchaseStatus.PENDING)
