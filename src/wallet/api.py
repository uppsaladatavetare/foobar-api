from django.db import transaction
from . import models, enums, exceptions


def get_wallet(owner_id, currency):
    """Return a wallet for given owner id.

    Creates a wallet if there is not one.
    """
    obj, created = models.Wallet.objects.get_or_create(
        owner_id=owner_id,
        currency=currency
    )
    return obj


def get_balance(owner_id, currency):
    """Return balance of the wallet and the wallet itself.

    Calculated by summing together all the PENDING/FINALIZED transactions
    in the wallet.
    """
    wallet_obj = get_wallet(owner_id, currency)
    qs = models.Wallet.objects.get(id=wallet_obj.id).transactions
    return wallet_obj, qs.balance()


def list_transactions(owner_id, currency, trx_type=None, trx_status=None,
                      start=None, limit=None):
    """Return a list of transactions matching the criteria."""
    wallet_obj = get_wallet(owner_id, currency)
    qs = models.Wallet.objects.get(id=wallet_obj.id).transactions
    if trx_type is not None:
        qs = qs.filter(trx_type=trx_type)
    if trx_status is not None:
        qs = qs.filter(trx_status=trx_status)
    return qs.all()[start:limit]


def get_transactions_by_ref(reference):
    """Return transactions with given reference."""
    return models.WalletTransaction.objects.filter(reference=reference)


def cancel_transaction(trx_id):
    """Cancels a transaction."""
    trx_obj = models.WalletTransaction.objects.get(id=trx_id)
    trx_obj.trx_status = enums.TrxStatus.CANCELED
    trx_obj.save()


@transaction.atomic
def withdraw(owner_id, amount, reference=None):
    """Withdraw given amount from the wallet.

    Throw InsufficientFunds if there is not enough money in the wallet.
    """
    assert amount.amount >= 0, "Cannot withdraw a negative amount of money"
    wallet_obj, balance = get_balance(owner_id, amount.currency)
    if amount > balance:
        raise exceptions.InsufficientFunds
    qs = models.Wallet.objects.get(id=wallet_obj.id).transactions
    trx_obj = qs.create(
        trx_type=enums.TrxType.OUTGOING,
        trx_status=enums.TrxStatus.FINALIZED,
        amount=amount,
        reference=reference
    )
    return trx_obj


@transaction.atomic
def deposit(owner_id, amount, reference=None):
    """Deposit given amount into the wallet."""
    assert amount.amount >= 0, "Cannot deposit a negative amount of money"
    wallet_obj = get_wallet(owner_id, amount.currency)
    qs = models.Wallet.objects.get(id=wallet_obj.id).transactions
    trx_obj = qs.create(
        trx_type=enums.TrxType.INCOMING,
        trx_status=enums.TrxStatus.FINALIZED,
        amount=amount,
        reference=reference
    )
    return trx_obj


@transaction.atomic
def transfer(debtor_id, creditor_id, amount, reference=None):
    """Withdraw money from debtor's wallet and deposit it into creditor's"""
    withdraw(debtor_id, amount, reference)
    deposit(creditor_id, amount, reference)
