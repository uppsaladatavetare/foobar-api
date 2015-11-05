# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foobar', '0006_auto_20151104_1402'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='purchase',
            options={'ordering': ['-date_created']},
        ),
        migrations.AlterField(
            model_name='purchase',
            name='account',
            field=models.ForeignKey(blank=True, to='foobar.Account', null=True, related_name='purchases'),
        ),
    ]
