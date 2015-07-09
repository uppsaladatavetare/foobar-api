# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import bitfield.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authtoken', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='scopes',
            field=bitfield.models.BitField((('read', 'Read scope'), ('write', 'Write scope'), ('accounts', 'Access to accounts'), ('categories', 'Access to categories'), ('products', 'Access to products'), ('purchases', 'Ability to make purchases'), ('wallet_trxs', 'Access to wallet transactions'), ('wallets', 'Access to wallets')), default=None),
        ),
    ]
