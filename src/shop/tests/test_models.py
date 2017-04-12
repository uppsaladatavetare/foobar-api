from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from unittest import mock

from . import factories
from .. import enums, models
from foobar.tests.factories import AccountFactory


class ProductTransactionModelTests(TestCase):
    @mock.patch('shop.models.validate_transition')
    def test_set_status(self, mock_validate_transition):
        product_trx = factories.ProductTrxFactory()
        factories.ProductTrxStatusFactory(
            trx=product_trx,
            status=enums.TrxStatus.PENDING
        )

        ref = AccountFactory()
        product_trx.set_status(
            status=enums.TrxStatus.FINALIZED,
            reference=ref
        )

        trx_status_qs = models.ProductTransactionStatus.objects.all()
        self.assertEqual(trx_status_qs.count(), 2)

        ct = ContentType.objects.get_for_model(ref)
        finalized_state = trx_status_qs.latest('date_created')
        self.assertEqual(finalized_state.reference_ct, ct)
        self.assertEqual(finalized_state.reference_id, ref.pk)

        self.assertEqual(product_trx.trx_status, enums.TrxStatus.FINALIZED)

        mock_validate_transition.assert_called_once_with(
            enums.TrxStatus,
            from_state=enums.TrxStatus.PENDING,
            to_state=enums.TrxStatus.FINALIZED
        )

    @mock.patch('shop.models.validate_transition')
    def test_set_status_no_reference(self, mock_validate_transition):
        product_trx = factories.ProductTrxFactory()
        factories.ProductTrxStatusFactory(
            trx=product_trx,
            status=enums.TrxStatus.PENDING
        )
        product_trx.set_status(status=enums.TrxStatus.FINALIZED)

        trx_status_qs = models.ProductTransactionStatus.objects.all()
        self.assertEqual(trx_status_qs.count(), 2)

        finalized_state = trx_status_qs.latest('date_created')
        self.assertIsNone(finalized_state.reference_ct)
        self.assertIsNone(finalized_state.reference_id)

        self.assertEqual(product_trx.trx_status, enums.TrxStatus.FINALIZED)

        mock_validate_transition.assert_called_once_with(
            enums.TrxStatus,
            from_state=enums.TrxStatus.PENDING,
            to_state=enums.TrxStatus.FINALIZED
        )
