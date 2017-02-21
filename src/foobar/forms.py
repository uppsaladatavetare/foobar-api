from django import forms
from djmoney.forms.fields import MoneyField
from foobar.wallet import api
from django.utils.translation import ugettext as _


class CorrectionForm(forms.Form):
    balance = MoneyField(label='Balance', min_value=0)
    comment = forms.CharField(label='Comment', max_length=128, required=False)


class DepositForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.owner_id = kwargs.pop('owner_id')
        super().__init__(*args, **kwargs)

    deposit_or_withdrawal = MoneyField(max_digits=10, decimal_places=2)
    comment = forms.CharField(max_length=128, required=False)

    def clean_deposit_or_withdrawal(self):
        data = self.cleaned_data['deposit_or_withdrawal']
        wallet, balance = api.get_balance(self.owner_id)
        if data.amount < 0 and -data > balance:
            raise forms.ValidationError(_('Not enough funds'))
        return data
