# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0003_auto_20151028_2246'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='card_id',
            field=models.BigIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='purchaseitem',
            name='amount_currency',
            field=djmoney.models.fields.CurrencyField(choices=[('SEK', 'Swedish Krona')], default='SEK', editable=False, max_length=3),
        ),
    ]
