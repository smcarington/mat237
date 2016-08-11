# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-07-09 22:45
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('Problems', '0047_auto_20160709_1843'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='markedquestion',
            options={'ordering': ['quiz', 'category'], 'verbose_name': 'Question'},
        ),
        migrations.AlterModelOptions(
            name='quiz',
            options={'verbose_name': 'Quiz', 'verbose_name_plural': 'Quizzes'},
        ),
        migrations.AlterField(
            model_name='announcement',
            name='expires',
            field=models.DateField(blank=True, default=datetime.datetime(2016, 7, 16, 22, 45, 17, 654307, tzinfo=utc), null=True),
        ),
    ]