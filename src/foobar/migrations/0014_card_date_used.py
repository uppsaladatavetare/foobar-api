# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-29 14:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0013_remove_account_card_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='date_used',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]