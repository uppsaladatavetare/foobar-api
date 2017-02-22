from django.test import TestCase
from moneyed import Money
from .. import api, models, enums, exceptions
from . import factories


class WalletTest(TestCase):
    def test_get_wallet(self):
        wallet_obj = factories.WalletFactory.create()
        item_obj = api.get_wallet(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(wallet_obj.balance, factories.WalletFactory.balance)
        self.assertIsNotNone(item_obj)
        self.assertEqual(models.Wallet.objects.count(), 1)

    def test_list_transactions(self):
        wallet_obj = factories.WalletFactory.create()
        for _ in range(5):
            factories.WalletTrxFactory.create(
                wallet=wallet_obj,
                trx_type=enums.TrxType.PENDING
            )
        trxs = api.list_transactions(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(len(trxs), 5)

        # test limit
        trxs = api.list_transactions(wallet_obj.owner_id, wallet_obj.currency,
                                     limit=1)
        self.assertEqual(len(trxs), 1)

        # test start
        trxs = api.list_transactions(wallet_obj.owner_id, wallet_obj.currency,
                                     start=1)
        self.assertEqual(len(trxs), 4)

        # test trx_status
        factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(10, 'SEK'),
            trx_type=enums.TrxType.FINALIZED
        )
        trxs = api.list_transactions(
            owner_id=wallet_obj.owner_id,
            currency=wallet_obj.currency,
            trx_type=enums.TrxType.FINALIZED
        )
        self.assertEqual(len(trxs), 1)

        # test trx_type
        factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            trx_type=enums.TrxType.FINALIZED,
            amount=-Money(10, 'SEK')
        )
        trxs = api.list_transactions(
            owner_id=wallet_obj.owner_id,
            currency=wallet_obj.currency,
            direction=enums.TrxDirection.OUTGOING
        )
        self.assertEqual(len(trxs), 1)
        trxs = api.list_transactions(
            owner_id=wallet_obj.owner_id,
            currency=wallet_obj.currency,
            direction=enums.TrxDirection.INCOMING
        )
        self.assertEqual(len(trxs), 6)

    def test_get_balance(self):
        wallet_obj = factories.WalletFactory.create()
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(0, wallet_obj.currency))
        self.assertEqual(balance1, balance2)
        # deposit 100 and mark as pending
        # pending and incoming transactions should not affect the balance
        factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            trx_type=enums.TrxType.PENDING,
            amount=Money(100, wallet_obj.currency)
        )
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(0, wallet_obj.currency))
        self.assertEqual(balance1, balance2)
        # deposit 100 and mark as finalized
        factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            trx_type=enums.TrxType.FINALIZED,
            amount=Money(100, wallet_obj.currency)
        )
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(100, wallet_obj.currency))
        self.assertEqual(balance1, balance2)
        # withdraw 50 and mark as pending
        factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            trx_type=enums.TrxType.FINALIZED,
            amount=-Money(50, wallet_obj.currency)
        )
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(50, wallet_obj.currency))
        self.assertEqual(balance1, balance2)
        # withdraw 50 and mark as finalized
        factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            trx_type=enums.TrxType.FINALIZED,
            amount=-Money(50, wallet_obj.currency)
        )
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(0, wallet_obj.currency))
        self.assertEqual(balance1, balance2)

    def test_set_balance(self):
        wallet_obj = factories.WalletFactory.create()
        factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            trx_type=enums.TrxType.FINALIZED,
            amount=Money(1000, wallet_obj.currency)
        )
        _, diff = api.set_balance(wallet_obj.owner_id, Money(800, 'SEK'))
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(diff.amount, -200)
        self.assertEqual(balance.amount, 800)
        _, diff = api.set_balance(wallet_obj.owner_id, Money(1000, 'SEK'))
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(diff.amount, 200)
        self.assertEqual(balance.amount, 1000)
        _, diff = api.set_balance(wallet_obj.owner_id, Money(1000, 'SEK'))
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(diff.amount, 0)
        self.assertEqual(balance.amount, 1000)

    def test_withdraw(self):
        wallet_obj = factories.WalletFactory.create()
        factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            trx_type=enums.TrxType.FINALIZED,
            amount=Money(100, wallet_obj.currency)
        )
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(100, wallet_obj.currency))
        trx_obj = api.withdraw(wallet_obj.owner_id,
                               Money(100, wallet_obj.currency))
        self.assertIsNotNone(trx_obj)
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(0, wallet_obj.currency))
        with self.assertRaises(exceptions.InsufficientFunds):
            api.withdraw(wallet_obj.owner_id, Money(1, wallet_obj.currency))

    def test_deposit(self):
        wallet_obj = factories.WalletFactory.create()
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(0, wallet_obj.currency))
        trx_obj = api.deposit(wallet_obj.owner_id,
                              Money(100, wallet_obj.currency))
        self.assertIsNotNone(trx_obj)
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(100, wallet_obj.currency))

    def test_transfer(self):
        wallet_obj1 = factories.WalletFactory.create(balance_currency='SEK')
        wallet_obj2 = factories.WalletFactory.create(balance_currency='SEK')
        factories.WalletTrxFactory.create(
            wallet=wallet_obj1,
            trx_type=enums.TrxType.FINALIZED,
            amount=Money(100, wallet_obj1.currency)
        )
        api.transfer(wallet_obj1.owner_id, wallet_obj2.owner_id,
                     Money(75, wallet_obj1.currency))
        _, balance1 = api.get_balance(wallet_obj1.owner_id,
                                      wallet_obj1.currency)
        _, balance2 = api.get_balance(wallet_obj2.owner_id,
                                      wallet_obj2.currency)
        self.assertEqual(balance1, Money(25, wallet_obj1.currency))
        self.assertEqual(balance2, Money(75, wallet_obj2.currency))
        with self.assertRaises(exceptions.InsufficientFunds):
            api.transfer(wallet_obj1.owner_id, wallet_obj2.owner_id,
                         Money(100, wallet_obj1.currency))

    def test_transaction_by_ref(self):
        wallet_obj = factories.WalletFactory.create()
        trx_obj1 = factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            trx_type=enums.TrxType.FINALIZED,
            amount=Money(100, wallet_obj.currency),
            reference='1337'
        )
        trx_objs = api.get_transactions_by_ref('1337')
        self.assertEqual(len(trx_objs), 1)
        self.assertEqual(trx_obj1.id, trx_objs[0].id)
        trx_objs = api.get_transactions_by_ref('7331')
        self.assertEqual(len(trx_objs), 0)

    def test_cancel_transaction(self):
        wallet_obj = factories.WalletFactory.create()
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        trx_obj1 = api.deposit(wallet_obj.owner_id,
                               Money(100, wallet_obj.currency))
        self.assertIsNotNone(trx_obj1)
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(100, wallet_obj.currency))
        trx_obj2 = api.cancel_transaction(trx_obj1.id)
        self.assertIsNotNone(trx_obj2)
        self.assertEqual(trx_obj2.trx_type, enums.TrxType.CANCELLATION)
        self.assertEqual(trx_obj2.internal_reference, trx_obj1)
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(0, wallet_obj.currency))

    def test_total_balance(self):
        wallet_obj1 = factories.WalletFactory.create()
        factories.WalletTrxFactory.create(
            wallet=wallet_obj1,
            trx_type=enums.TrxType.FINALIZED,
            amount=Money(100, wallet_obj1.currency)
        )
        wallet_obj2 = factories.WalletFactory.create()
        factories.WalletTrxFactory.create(
            wallet=wallet_obj2,
            trx_type=enums.TrxType.FINALIZED,
            amount=Money(500, wallet_obj1.currency)
        )
        factories.WalletTrxFactory.create(
            wallet=wallet_obj2,
            trx_type=enums.TrxType.PENDING,
            amount=Money(500, wallet_obj1.currency)
        )
        factories.WalletTrxFactory.create(
            wallet=wallet_obj2,
            trx_type=enums.TrxType.FINALIZED,
            amount=-Money(100, wallet_obj1.currency)
        )
        total = api.total_balance(wallet_obj1.currency)
        self.assertEqual(total, Money(500, wallet_obj1.currency))
        total = api.total_balance(wallet_obj1.currency,
                                  exclude_ids=[wallet_obj1.owner_id])
        self.assertEqual(total, Money(400, wallet_obj1.currency))
