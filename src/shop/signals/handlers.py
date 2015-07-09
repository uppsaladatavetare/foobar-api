from django.db.models.signals import post_save
from django.dispatch import receiver
from .. import models


@receiver(post_save, sender=models.ProductTransaction)
def update_cached_product_quantity(sender, instance, created, **kwargs):
    # Assume `created` as neither updates nor deletes should ever happen
    # to product transactions.
    assert created
    product_obj = instance.product
    product_obj.qty += instance.qty
    product_obj.save()
