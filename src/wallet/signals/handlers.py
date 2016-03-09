from django.db.models.signals import post_save
from django.dispatch import receiver
from .. import models


@receiver(post_save, sender=models.WalletTransaction)
def update_wallet_balance(sender, instance, created, **kwargs):
    wallet_obj = instance.wallet
    if created and instance.countable:
        # A transaction has been created. If the transaction is finalized,
        # we simply add it to the wallet balance.
        wallet_obj.balance += instance.signed_amount
    elif not created:
        # A transaction has been updated, so we simply recalculate
        # the wallet balance.
        wallet_obj.balance = wallet_obj.transactions.balance()
    wallet_obj.save()
