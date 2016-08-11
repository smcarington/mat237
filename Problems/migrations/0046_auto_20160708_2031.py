# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-07-09 00:31
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('Problems', '0045_auto_20160708_1927'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentvote',
            name='question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Problems.PollQuestion'),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='expires',
            field=models.DateField(blank=True, default=datetime.datetime(2016, 7, 30, 0, 31, 42, 731302, tzinfo=utc), null=True),
        ),
    ]