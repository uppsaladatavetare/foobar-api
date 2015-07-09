# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallettransaction',
            name='amount_currency',
            field=djmoney.models.fields.CurrencyField(choices=[('SEK', 'Swedish Krona')], default='SEK', editable=False, max_length=3),
        ),
    ]
