# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0005_auto_20151104_1054'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='email',
            field=models.CharField(null=True, blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='account',
            name='name',
            field=models.CharField(null=True, blank=True, max_length=128),
        ),
    ]
