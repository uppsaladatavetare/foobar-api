# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-28 11:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0017_auto_20170222_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplierproduct',
            name='units',
            field=models.SmallIntegerField(default=1),
        ),
    ]
