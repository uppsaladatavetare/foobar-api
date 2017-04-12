from django.db.models.signals import post_save
from django.dispatch import receiver

from .. import models, enums


@receiver(post_save, sender=models.ProductTransactionStatus)
def update_cached_product_quantity(sender, instance, created, **kwargs):
    # Updating product transaction statuses is not supported
    assert created

    trx_obj = instance.trx
    product_obj = instance.trx.product
    if instance.status == enums.TrxStatus.PENDING:
        # A pending transaction has been created, so updating of the product
        # quantity is a simple matter of increasing product qty with
        # transaction qty.
        product_obj.qty += trx_obj.qty

    elif instance.status == enums.TrxStatus.CANCELED:
        # A transaction has been modified, so it may have changed status.
        # We solve it in a naive way, by recounting all the transactions.
        product_obj.qty -= trx_obj.qty

    else:
        return

    product_obj.save()
