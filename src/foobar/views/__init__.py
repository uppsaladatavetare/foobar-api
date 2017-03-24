from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from foobar.wallet.api import get_wallet
from .forms import CorrectionForm, DepositForm, EditProfileForm
from .decorators import token_required
from .. import api


@staff_member_required
@permission_required('foobar.change_account')
def account_for_card(request, card_id):
    account_obj = api.get_account_by_card(card_id)
    if account_obj is None:
        messages.add_message(request, messages.ERROR,
                             _('No account has been found for given card.'))
        return redirect('admin:foobar_account_changelist')

    return redirect('admin:foobar_account_change', account_obj.id)


@staff_member_required
@permission_required('wallet.change_wallet')
def wallet_management(request, obj_id):
    form_class = CorrectionForm(request.POST or None)
    form_class1 = DepositForm(request.POST or None, owner_id=obj_id)
    wallet = get_wallet(obj_id)
    if request.method == 'POST':
        if 'save_correction' in request.POST:
            if form_class.is_valid():
                api.calculate_correction(
                    form_class.cleaned_data['balance'],
                    obj_id,
                    request.user,
                    form_class.cleaned_data['comment']
                )
                messages.add_message(request,
                                     messages.INFO,
                                     _('Correction was successfully saved.'))
                return HttpResponseRedirect(request.path)

        elif 'save_deposit' in request.POST:
            if form_class1.is_valid():
                api.make_deposit_or_withdrawal(
                    form_class1.cleaned_data['deposit_or_withdrawal'],
                    obj_id,
                    request.user,
                    form_class1.cleaned_data['comment']
                )
                messages.add_message(request,
                                     messages.INFO,
                                     _('Successfully saved.'))
                return HttpResponseRedirect(request.path)

    return render(request,
                  'admin/wallet_management.html',
                  {'wallet': wallet,
                   'form_class': form_class,
                   'form_class1': form_class1})


@token_required
def edit_profile(request, account):
    form_class = EditProfileForm(
        request.POST or None,
        initial={'name': account.name, 'email': account.email}
    )

    if request.method == 'POST' and form_class.is_valid():
        api.update_account(
            account.id,
            name=form_class.cleaned_data['name'],
            email=form_class.cleaned_data['email']
        )
        messages.add_message(request, messages.INFO, _('Successfully Saved'))
    return render(request, "profile/success.html", {'form': form_class})
