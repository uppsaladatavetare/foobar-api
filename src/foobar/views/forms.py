from django import forms
from djmoney.forms.fields import MoneyField
from foobar.wallet import api as wallet_api
from django.utils.translation import ugettext as _
from .. import api


class CorrectionForm(forms.Form):
    balance = MoneyField(label=_('Balance'), min_value=0)
    comment = forms.CharField(label=_('Comment'),
                              max_length=128,
                              required=False)


class DepositForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.owner_id = kwargs.pop('owner_id')
        super().__init__(*args, **kwargs)

    deposit_or_withdrawal = MoneyField(max_digits=10, decimal_places=2)
    comment = forms.CharField(max_length=128, required=False)

    def clean_deposit_or_withdrawal(self):
        data = self.cleaned_data['deposit_or_withdrawal']
        wallet, balance = wallet_api.get_balance(self.owner_id)
        if data.amount < 0 and -data > balance:
            raise forms.ValidationError(_('Not enough funds'))
        return data


class EditProfileForm(forms.Form):
    name = forms.CharField(label=_('Account Name'), max_length=128)
    email = forms.EmailField(label=_('E-mail'))

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        account = api.get_account(email=email)
        if account is not None and account.id != self.account.id:
            raise forms.ValidationError(_('This e-mail is already in use.'))
        return email
