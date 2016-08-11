# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-07-08 23:22
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('Problems', '0041_auto_20160708_1916'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='expires',
            field=models.DateField(blank=True, default=datetime.datetime(2016, 7, 29, 23, 22, 53, 28785, tzinfo=utc), null=True),
        ),
        migrations.AlterField(
            model_name='studentvote',
            name='vote',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='Problems.PollChoice'),
        ),
    ]