# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0004_auto_20151103_2214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='card_id',
            field=models.CharField(unique=True, max_length=20),
        ),
    ]
