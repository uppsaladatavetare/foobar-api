from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from foobar.wallet import api as wallet_api
from .decorators import token_required
from .forms import CorrectionForm, DepositForm, EditProfileForm
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
    wallet = wallet_api.get_wallet(obj_id)
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


@method_decorator(token_required, name='dispatch')
class BaseProfileView(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        self._dispatch_kwargs = kwargs
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wallet_obj, balance = wallet_api.get_balance(context['account'].id)
        context['balance'] = balance
        return context

    def token_reverse(self, viewname, urlconf=None, args=None, kwargs=None,
                      current_app=None):
        kwargs = kwargs or {}
        kwargs['token'] = self._dispatch_kwargs['token']
        return reverse(viewname, urlconf, args, kwargs, current_app)


class ProfileView(BaseProfileView):
    template_name = 'profile/home.html'


class EditProfileView(BaseProfileView):
    template_name = 'profile/edit.html'

    def get(self, request, token, account):
        form = EditProfileForm(
            initial={'name': account.name, 'email': account.email},
            account=account
        )
        context = {'form': form}
        return self.render_to_response(context)

    def post(self, request, token, account):
        form = EditProfileForm(request.POST, account=account)
        if form.is_valid():
            api.update_account(
                account.id,
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email']
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                _('Your profile has been updated.')
            )
            url = self.token_reverse('profile-home')
            return HttpResponseRedirect(url)
        context = {'form': form}
        return self.render_to_response(context)
