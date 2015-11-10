from django.db.models.signals import post_save
from django.dispatch import receiver
from .. import models


@receiver(post_save, sender=models.ProductTransaction)
def update_cached_product_quantity(sender, instance, created, **kwargs):
    product_obj = instance.product
    if created:
        # A transaction has been created, so updating of the product quantity
        # is a simple matter of increasing product qty with transaction qty.
        product_obj.qty += instance.qty
    else:
        # A transaction has been modified, so it may have changed status.
        # We solve it in a naive way, by recounting all the transactions.
        product_obj.qty = product_obj.transactions.quantity()
    product_obj.save()
