# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-05 17:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0019_auto_20170228_2012'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseStockLevel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('level', models.SmallIntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='basestocklevel',
            name='product',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='shop.Product'),
        ),
    ]
