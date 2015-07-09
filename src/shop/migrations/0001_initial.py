# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import enumfields.fields
import shop.models
import shop.enums
import djmoney.models.fields
from decimal import Decimal
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('date_created', models.DateTimeField(null=True, verbose_name='date created', auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True, null=True, verbose_name='date modified')),
                ('id', models.UUIDField(serialize=False, primary_key=True, default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=64)),
                ('code', models.CharField(max_length=13)),
                ('description', models.TextField(null=True, blank=True)),
                ('image', models.ImageField(null=True, blank=True, upload_to=shop.models.generate_product_filename)),
                ('price_currency', djmoney.models.fields.CurrencyField(max_length=3, choices=[('SEK', 'SEK')], default='SEK', editable=False)),
                ('price', djmoney.models.fields.MoneyField(currency_choices=(('SEK', 'SEK'),), decimal_places=2, default_currency='SEK', default=Decimal('0.0'), max_digits=10)),
                ('active', models.BooleanField(default=True)),
                ('qty', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'products',
                'verbose_name': 'product',
            },
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.UUIDField(serialize=False, primary_key=True, default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=64)),
                ('image', models.ImageField(null=True, blank=True, upload_to='')),
            ],
            options={
                'verbose_name_plural': 'categories',
                'verbose_name': 'category',
            },
        ),
        migrations.CreateModel(
            name='ProductTransaction',
            fields=[
                ('date_created', models.DateTimeField(null=True, verbose_name='date created', auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True, null=True, verbose_name='date modified')),
                ('id', models.UUIDField(serialize=False, primary_key=True, default=uuid.uuid4, editable=False)),
                ('qty', models.IntegerField()),
                ('trx_type', enumfields.fields.EnumIntegerField(enum=shop.enums.TrxType)),
                ('product', models.ForeignKey(related_name='transactions', to='shop.Product')),
            ],
            options={
                'verbose_name_plural': 'transactions',
                'verbose_name': 'transaction',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(blank=True, to='shop.ProductCategory', null=True),
        ),
    ]
