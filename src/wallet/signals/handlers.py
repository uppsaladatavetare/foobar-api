from django.dispatch import receiver

from .. import models, enums
from .signals import status_change


@receiver(status_change, sender=models.WalletTransactionStatus)
def update_wallet_balance(sender, instance, from_status,
                          to_status, direction, **kwargs):
    multiplier = enums.get_direction_multiplier(
        enum=enums.TrxStatus,
        from_state=from_status,
        to_state=to_status,
        direction=direction
    )

    wallet_obj = instance.trx.wallet
    wallet_obj.balance += (multiplier * instance.trx.amount)
    wallet_obj.save()
