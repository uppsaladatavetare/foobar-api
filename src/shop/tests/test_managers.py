from django.test import TestCase

from . import factories
from .. import enums, models


class ProductTrxQuerySetTests(TestCase):
    def test_get_finalized(self):
        trx_obj1 = factories.ProductTrxFactory()
        factories.ProductTrxStatusFactory(
            trx=trx_obj1,
            status=enums.TrxStatus.PENDING
        )
        factories.ProductTrxStatusFactory(
            trx=trx_obj1,
            status=enums.TrxStatus.FINALIZED
        )

        trx_obj2 = factories.ProductTrxFactory()
        factories.ProductTrxStatusFactory(
            trx=trx_obj2,
            status=enums.TrxStatus.PENDING
        )
        factories.ProductTrxStatusFactory(
            trx=trx_obj2,
            status=enums.TrxStatus.FINALIZED
        )
        factories.ProductTrxStatusFactory(
            trx=trx_obj2,
            status=enums.TrxStatus.CANCELED
        )

        trx_obj3 = factories.ProductTrxFactory()
        factories.ProductTrxStatusFactory(
            trx=trx_obj3,
            status=enums.TrxStatus.PENDING
        )

        finalized = models.ProductTransaction.objects.finalized()

        self.assertEqual(finalized.count(), 1)
        self.assertEqual(finalized.first().trx_status,
                         enums.TrxStatus.FINALIZED)
        self.assertEqual(finalized.first().product.pk,
                         trx_obj1.product.pk)
