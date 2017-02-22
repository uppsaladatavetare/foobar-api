from django.db.models.signals import post_save
from django.dispatch import receiver
from .. import models


@receiver(post_save, sender=models.WalletTransaction)
def update_wallet_balance(sender, instance, created, **kwargs):
    wallet_obj = instance.wallet
    if created and instance.countable:
        wallet_obj.balance += instance.signed_amount
        wallet_obj.save()
