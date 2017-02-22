from django.test import TestCase
from wallet.tests.factories import WalletFactory, WalletTrxFactory
from wallet.enums import TrxType
from moneyed import Money
from django.contrib.auth.models import User
from django.urls import reverse
from unittest import mock


class FoobarViewTest(TestCase):
    @mock.patch('foobar.api.calculate_correction')
    @mock.patch('foobar.api.make_deposit_or_withdrawal')
    def test_wallet_management(self, mock_deposit_withdrawal, mock_correction):
        user = User.objects.create_superuser(
            'the_baconator', 'bacon@foobar.com', '123'
        )
        wallet_obj = WalletFactory.create()
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1200, 'SEK'),
            trx_type=TrxType.FINALIZED
        )
        url = reverse('wallet_management',
                      kwargs={'obj_id': wallet_obj.owner_id})
        cl = self.client
        cl.login(username='the_baconator', password='123')
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
                                           user,
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
            user,
            'test')
