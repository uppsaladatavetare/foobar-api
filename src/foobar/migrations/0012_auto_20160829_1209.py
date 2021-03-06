# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-29 12:09
from __future__ import unicode_literals

from django.db import migrations

def migrate_cards(apps, schema_editor):
    Account = apps.get_model('foobar', 'Account')
    Card = apps.get_model('foobar', 'Card')
    for account_obj in Account.objects.all():
        Card.objects.create(
            account=account_obj,
            number=account_obj.card_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0011_card'),
    ]

    operations = [
        migrations.RunPython(migrate_cards)
    ]
