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
        trxs = factories.WalletTrxFactory.create_batch(
            wallet=wallet_obj,
            size=5
        )
        [x.set_status(enums.TrxStatus.PENDING) for x in trxs]
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
        factories.WalletTrxWithStatusFactory.create(
            wallet=wallet_obj,
            amount=Money(10, 'SEK'),
            states__status=enums.TrxStatus.FINALIZED
        )
        trxs = api.list_transactions(
            owner_id=wallet_obj.owner_id,
            currency=wallet_obj.currency,
            status=enums.TrxStatus.FINALIZED
        )
        self.assertEqual(len(trxs), 1)

        # test trx_type
        factories.WalletTrxWithStatusFactory.create(
            wallet=wallet_obj,
            amount=-Money(10, 'SEK'),
            states__status=enums.TrxStatus.FINALIZED
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
        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(100, wallet_obj.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(0, wallet_obj.currency))
        self.assertEqual(balance1, balance2)
        # deposit 100 and mark as finalized
        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(100, wallet_obj.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(100, wallet_obj.currency))
        self.assertEqual(balance1, balance2)
        # withdraw 50 and mark as pending
        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=-Money(50, wallet_obj.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(50, wallet_obj.currency))
        self.assertEqual(balance1, balance2)
        # withdraw 50 and mark as finalized
        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=-Money(50, wallet_obj.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(0, wallet_obj.currency))
        self.assertEqual(balance1, balance2)

        trx_obj.set_status(enums.TrxStatus.CANCELLATION)
        _, balance1 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        _, balance2 = api.get_balance(wallet_obj.owner_id, wallet_obj.currency,
                                      cached=False)
        self.assertEqual(balance1, Money(50, wallet_obj.currency))
        self.assertEqual(balance1, balance2)

    def test_set_balance(self):
        wallet_obj = factories.WalletFactory.create()
        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, wallet_obj.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

        _, diff = api.set_balance(wallet_obj.owner_id, Money(800, 'SEK'))
        self.assertEqual(trx_obj.status, enums.TrxStatus.FINALIZED)
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(diff.amount, -200)
        self.assertEqual(balance.amount, 800)

        _, diff = api.set_balance(wallet_obj.owner_id, Money(1000, 'SEK'))
        self.assertEqual(trx_obj.status, enums.TrxStatus.FINALIZED)
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(diff.amount, 200)
        self.assertEqual(balance.amount, 1000)

        trx_obj, diff = api.set_balance(wallet_obj.owner_id,
                                        Money(1000, 'SEK'))
        self.assertIsNone(trx_obj)
        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(diff.amount, 0)
        self.assertEqual(balance.amount, 1000)

    def test_withdraw(self):
        wallet_obj = factories.WalletFactory.create()
        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(100, wallet_obj.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(100, wallet_obj.currency))

        trx_obj = api.withdraw(wallet_obj.owner_id,
                               Money(100, wallet_obj.currency))
        self.assertIsNotNone(trx_obj)
        self.assertEqual(trx_obj.status, enums.TrxStatus.PENDING)

        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(0, wallet_obj.currency))
        with self.assertRaises(exceptions.InsufficientFunds):
            api.withdraw(wallet_obj.owner_id, Money(1, wallet_obj.currency))

        trx_obj = api.finalize_transaction(trx_obj.pk)
        self.assertEqual(trx_obj.status, enums.TrxStatus.FINALIZED)

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
        self.assertEqual(trx_obj.status, enums.TrxStatus.PENDING)

        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(0, wallet_obj.currency))

        trx_obj = api.finalize_transaction(trx_obj.pk)
        self.assertEqual(trx_obj.status, enums.TrxStatus.FINALIZED)

        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(100, wallet_obj.currency))

    def test_transfer(self):
        wallet_obj1 = factories.WalletFactory.create(balance_currency='SEK')
        wallet_obj2 = factories.WalletFactory.create(balance_currency='SEK')
        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj1,
            amount=Money(100, wallet_obj1.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

        withdrawal_trx, deposit_trx = api.transfer(
            wallet_obj1.owner_id,
            wallet_obj2.owner_id,
            Money(75, wallet_obj1.currency)
        )
        self.assertEqual(withdrawal_trx.status, enums.TrxStatus.PENDING)
        self.assertEqual(deposit_trx.status, enums.TrxStatus.PENDING)

        _, balance1 = api.get_balance(wallet_obj1.owner_id,
                                      wallet_obj1.currency)
        _, balance2 = api.get_balance(wallet_obj2.owner_id,
                                      wallet_obj2.currency)
        self.assertEqual(balance1, Money(25, wallet_obj1.currency))
        self.assertEqual(balance2, Money(0, wallet_obj2.currency))

        with self.assertRaises(exceptions.InsufficientFunds):
            api.transfer(wallet_obj1.owner_id, wallet_obj2.owner_id,
                         Money(30, wallet_obj1.currency))

        withdrawal_trx = api.finalize_transaction(withdrawal_trx.pk)
        deposit_trx = api.finalize_transaction(deposit_trx.pk)

        self.assertEqual(withdrawal_trx.status, enums.TrxStatus.FINALIZED)
        self.assertEqual(deposit_trx.status, enums.TrxStatus.FINALIZED)

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
        trx_obj1 = factories.WalletTrxWithStatusFactory.create(
            wallet=wallet_obj,
            amount=Money(100, wallet_obj.currency),
            reference='1337',
            states__status=enums.TrxStatus.FINALIZED,
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
        self.assertEqual(trx_obj1.status, enums.TrxStatus.PENDING)

        trx_obj1 = api.finalize_transaction(trx_obj1.pk)
        self.assertEqual(trx_obj1.status, enums.TrxStatus.FINALIZED)

        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(100, wallet_obj.currency))

        trx_obj2 = api.cancel_transaction(trx_obj1.id)
        self.assertIsNotNone(trx_obj2)
        self.assertEqual(trx_obj2.status, enums.TrxStatus.CANCELLATION)

        _, balance = api.get_balance(wallet_obj.owner_id, wallet_obj.currency)
        self.assertEqual(balance, Money(0, wallet_obj.currency))

    def test_total_balance(self):
        wallet_obj1 = factories.WalletFactory.create()
        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj1,
            amount=Money(100, wallet_obj1.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

        wallet_obj2 = factories.WalletFactory.create()
        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj2,
            amount=Money(500, wallet_obj1.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj2,
            amount=Money(500, wallet_obj1.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)

        trx_obj = factories.WalletTrxFactory.create(
            wallet=wallet_obj2,
            amount=-Money(100, wallet_obj1.currency)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

        total = api.total_balance(wallet_obj1.currency)
        self.assertEqual(total, Money(500, wallet_obj1.currency))
        total = api.total_balance(wallet_obj1.currency,
                                  exclude_ids=[wallet_obj1.owner_id])
        self.assertEqual(total, Money(400, wallet_obj1.currency))

    def test_finalize_transaction(self):
        wallet_obj = factories.WalletFactory.create()
        currency = wallet_obj.currency

        trx_obj = api.deposit(wallet_obj.owner_id, Money(100, currency))
        self.assertEqual(trx_obj.status, enums.TrxStatus.PENDING)

        _, balance = api.get_balance(wallet_obj.owner_id, currency)
        self.assertEqual(balance, Money(0, currency))

        trx_obj = api.finalize_transaction(trx_obj.pk)
        self.assertEqual(trx_obj.status, enums.TrxStatus.FINALIZED)

        _, balance = api.get_balance(wallet_obj.owner_id, currency)
        self.assertEqual(balance, Money(100, currency))

        trx_obj1 = api.deposit(wallet_obj.owner_id, Money(200, currency))
        trx_obj2 = api.deposit(wallet_obj.owner_id, Money(300, currency))
        self.assertEqual(trx_obj1.status, enums.TrxStatus.PENDING)
        self.assertEqual(trx_obj2.status, enums.TrxStatus.PENDING)

        _, balance = api.get_balance(wallet_obj.owner_id, currency)
        self.assertEqual(balance, Money(100, currency))

        trxs = api.finalize_transactions([trx_obj1.pk, trx_obj2.pk])
        for trx_obj in trxs:
            self.assertEqual(trx_obj.status, enums.TrxStatus.FINALIZED)

        _, balance = api.get_balance(wallet_obj.owner_id, currency)
        self.assertEqual(balance, Money(600, currency))
