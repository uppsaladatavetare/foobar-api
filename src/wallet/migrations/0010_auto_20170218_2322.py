# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-18 23:22
from __future__ import unicode_literals

from django.db import migrations
import enumfields.fields
import wallet.enums
import enum


class TrxType(enum.Enum):
    FINALIZED = 0
    PENDING = 1
    CANCELLATION = 2


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0009_remove_wallettransaction_trx_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallettransaction',
            name='trx_type',
            field=enumfields.fields.EnumIntegerField(default=0, enum=TrxType),
        ),
    ]
