# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='date created'),
        ),
        migrations.AddField(
            model_name='account',
            name='date_modified',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='date modified'),
        ),
    ]
