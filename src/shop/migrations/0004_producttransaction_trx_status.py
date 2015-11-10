# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shop.enums
import enumfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_auto_20151028_1621'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttransaction',
            name='trx_status',
            field=enumfields.fields.EnumIntegerField(default=0, enum=shop.enums.TrxStatus),
        ),
    ]
