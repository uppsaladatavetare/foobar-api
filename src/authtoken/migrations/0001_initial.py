# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import bitfield.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('scopes', bitfield.models.BitField((('read', 'Read scope'), ('write', 'Write scope'), ('accounts', 'Access to accounts'), ('categories', 'Access to categories'), ('products', 'Access to products'), ('purchases', 'Ability to make purchases'), ('wallet_trxs', 'Acess to wallet transactions'), ('wallets', 'Access to wallets')), default=None)),
            ],
        ),
    ]
