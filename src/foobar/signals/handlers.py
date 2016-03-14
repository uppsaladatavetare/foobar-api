from django.db.models.signals import post_save
from django.dispatch import receiver
from .. import models


@receiver(post_save, sender=models.PurchaseItem)
def update_wallet_balance(sender, instance, created, **kwargs):
    # Updating purchased items is not supported
    assert created
    purchase_obj = instance.purchase
    purchase_obj.amount += instance.qty * instance.amount
    purchase_obj.save()
