# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_producttransaction_trx_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttransaction',
            name='reference',
            field=models.CharField(blank=True, null=True, max_length=128),
        ),
    ]
