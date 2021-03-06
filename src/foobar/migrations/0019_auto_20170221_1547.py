# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-21 15:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0018_auto_20170220_1322'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='walletlogentry',
            options={'verbose_name': 'wallet log entry', 'verbose_name_plural': 'wallet log entries'},
        ),
        migrations.AlterField(
            model_name='walletlogentry',
            name='wallet',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='log_entries', to='wallet.Wallet'),
        ),
    ]
