from functools import partial
from django.conf import settings

from wallet import api

DEFAULT_CURRENCY = settings.DEFAULT_CURRENCY

get_wallet = partial(api.get_wallet, currency=DEFAULT_CURRENCY)
get_balance = partial(api.get_balance, currency=DEFAULT_CURRENCY)
set_balance = api.set_balance
list_transactions = partial(api.list_transactions, currency=DEFAULT_CURRENCY)
total_balance = partial(api.total_balance, currency=DEFAULT_CURRENCY)
withdraw = api.withdraw
deposit = api.deposit
transfer = api.transfer
get_transactions_by_ref = api.get_transactions_by_ref
cancel_transaction = api.cancel_transaction
