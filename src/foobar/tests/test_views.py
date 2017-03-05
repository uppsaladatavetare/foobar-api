from unittest import mock
from moneyed import Money
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from wallet.tests.factories import WalletFactory, WalletTrxFactory
from wallet.enums import TrxType
from . import factories


class FoobarViewTest(TestCase):
    TESTUSER_NAME = 'the_baconator'
    TESTUSER_PASS = '123'

    def setUp(self):
        self.user = User.objects.create_superuser(
            self.TESTUSER_NAME,
            'bacon@foobar.com',
            self.TESTUSER_PASS
        )
        self.client.login(
            username=self.TESTUSER_NAME,
            password=self.TESTUSER_PASS
        )

    @mock.patch('foobar.api.get_account')
    def test_account_for_card(self, mock_get_account):
        url = reverse('account_for_card', kwargs={'card_id': 1337})
        mock_get_account.return_value = None
        response = self.client.get(url, follow=True)
        self.assertRedirects(
            response,
            reverse('admin:foobar_account_changelist')
        )
        self.assertEqual(len(response.context['messages']), 1)
        account = factories.AccountFactory()
        mock_get_account.return_value = account
        response = self.client.get(url, follow=True)
        self.assertRedirects(
            response,
            reverse('admin:foobar_account_change', args=(account.id,))
        )
        self.assertEqual(len(response.context['messages']), 0)

    @mock.patch('foobar.api.calculate_correction')
    @mock.patch('foobar.api.make_deposit_or_withdrawal')
    def test_wallet_management(self, mock_deposit_withdrawal, mock_correction):
        wallet_obj = WalletFactory.create()
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1200, 'SEK'),
            trx_type=TrxType.FINALIZED
        )
        url = reverse('wallet_management',
                      kwargs={'obj_id': wallet_obj.owner_id})
        cl = self.client
        # Test that deposit or withdrawal
        # is not called if balance will get negative
        response = cl.post(url,
                           {'deposit_or_withdrawal_1': ['SEK'],
                            'save_deposit': ['Submit'],
                            'comment': ['test'],
                            'deposit_or_withdrawal_0': ['-3000']})
        mock_deposit_withdrawal.assert_not_called()
        # Test that page can be found
        response = cl.get(url)
        self.assertEqual(response.status_code, 200)
        # Test that correction form post is correct and
        # calls function with correct params
        response = cl.post(url,
                           {'save_correction': ['Submit'],
                            'balance_1': ['SEK'],
                            'comment': ['test'],
                            'balance_0': ['1000']})
        mock_correction.assert_called_with(Money(1000, 'SEK'),
                                           wallet_obj.owner_id,
                                           self.user,
                                           'test')
        # Test that deposit or withdrawal form post is correct and
        # calls fucnction with correct params
        response = cl.post(url,
                           {'deposit_or_withdrawal_1': ['SEK'],
                            'save_deposit': ['Submit'],
                            'comment': ['test'],
                            'deposit_or_withdrawal_0': ['100']})
        mock_deposit_withdrawal.assert_called_with(
            Money(100, 'SEK'),
            wallet_obj.owner_id,
            self.user,
            'test')
