from django.contrib.auth.decorators import permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from . import api


@staff_member_required
@permission_required('foobar.change_account')
def account_for_card(request, card_id):
    account_obj = api.get_account(card_id)
    return redirect('admin:foobar_account_change', account_obj.id)
