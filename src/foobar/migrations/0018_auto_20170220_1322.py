# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-20 13:22
from __future__ import unicode_literals

from decimal import Decimal
from django.db import migrations
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0017_walletlogentry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='walletlogentry',
            name='pre_balance',
            field=djmoney.models.fields.MoneyField(decimal_places=2, default=Decimal('0.0'), max_digits=10, verbose_name='old balance'),
        ),
    ]
