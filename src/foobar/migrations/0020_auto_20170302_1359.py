# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-02 13:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0019_auto_20170221_1547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
