from django.db import models
from . import enums


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)


class ProductTrxQuerySet(models.QuerySet):
    def restocks(self):
        return self.filter(trx_type__in=[
            enums.TrxType.INVENTORY,
            enums.TrxType.CORRECTION
        ])

    def finalized(self):
        # Filter out the latest status timestamps for every transaction
        stamps = self.annotate(
            latest_stamp=models.Max('states__date_created')
        ).values_list('latest_stamp', flat=True)

        states = self.filter(
            states__date_created__in=stamps,
            states__status=enums.TrxStatus.FINALIZED
        )

        return states
