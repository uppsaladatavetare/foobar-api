# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-13 20:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion
from django.db.models import Sum
from django.utils.timezone import timedelta
import enumfields.fields
import foobar.enums
import uuid
import enum
from moneyed import Money


class PurchaseStatusOld(enum.Enum):
    FINALIZED = 0
    CANCELED = 1


class PurchaseStatus(enum.Enum):
    FINALIZED = 0
    CANCELED = 1
    PENDING = 2


class TrxType(enum.Enum):
    FINALIZED = 0
    PENDING = 1
    CANCELLATION = 2


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    purchases = apps.get_model('foobar', 'purchase')
    status_model = apps.get_model('foobar', 'purchasestatus')

    qs = purchases.objects.all()

    WalletTransaction = apps.get_model("wallet", "WalletTransaction")
    pre_balance = WalletTransaction.objects \
        .exclude(trx_type=TrxType.PENDING) \
        .aggregate(amount=Sum('amount'))['amount'] or Money(0, 'SEK')

    for purchase in qs:
        # Make sure we simulate that any PENDING was created
        # before FINALIZED
        status_model.objects.create(
            date_created=(purchase.date_created - timedelta(milliseconds=100)),
            purchase=purchase,
            status=PurchaseStatus.PENDING
        )

        if purchase.status.value == PurchaseStatusOld.FINALIZED.value:
            status = PurchaseStatus.FINALIZED
        else:
            status = PurchaseStatus.CANCELED

        status_model.objects.create(
            date_created=purchase.date_created,
            purchase=purchase,
            status=status
        )

    post_balance = WalletTransaction.objects \
        .exclude(trx_type=TrxType.PENDING) \
        .aggregate(amount=Sum('amount'))['amount'] or Money(0, 'SEK')
    # Make sure that the total balance in the system has not changed
    assert pre_balance == post_balance


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0020_auto_20170302_1359'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseStatus',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='date created')),
                ('date_modified', models.DateTimeField(auto_now=True, null=True, verbose_name='date modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', enumfields.fields.EnumIntegerField(default=2, enum=foobar.enums.PurchaseStatus)),
                ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='states', to='foobar.Purchase')),
            ],
            options={
                'verbose_name_plural': 'purchase statuses',
                'verbose_name': 'purchase status',
            },
        ),
        migrations.AlterModelOptions(
            name='purchasestatus',
            options={'ordering': ('-date_created',), 'verbose_name': 'purchase status', 'verbose_name_plural': 'purchase statuses'},
        ),
        migrations.RunPython(forwards_func),

        migrations.RemoveField(
            model_name='purchase',
            name='status',
        ),
        migrations.AlterField(
            model_name='account',
            name='date_created',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False, null=True, verbose_name='date created'),
        ),
        migrations.AlterField(
            model_name='card',
            name='date_created',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False, null=True, verbose_name='date created'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='date_created',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False, null=True, verbose_name='date created'),
        ),
        migrations.AlterField(
            model_name='purchasestatus',
            name='date_created',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False, null=True, verbose_name='date created'),
        ),
        migrations.AlterField(
            model_name='walletlogentry',
            name='date_created',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False, null=True, verbose_name='date created'),
        ),
    ]