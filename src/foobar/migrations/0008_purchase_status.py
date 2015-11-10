# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import foobar.enums
import enumfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0007_auto_20151105_1701'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='status',
            field=enumfields.fields.EnumIntegerField(enum=foobar.enums.PurchaseStatus, default=0),
        ),
    ]
