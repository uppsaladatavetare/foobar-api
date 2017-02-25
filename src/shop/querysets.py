from django.db import models
from . import enums


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)


class ProductTrxQuerySet(models.QuerySet):
    def finalized(self):
        return self.filter(trx_status=enums.TrxStatus.FINALIZED)

    def restocks(self):
        return self.filter(trx_type__in=[
            enums.TrxType.INVENTORY,
            enums.TrxType.CORRECTION
        ])

    def quantity(self):
        return self.finalized().aggregate(qty=models.Sum('qty'))['qty'] or 0
