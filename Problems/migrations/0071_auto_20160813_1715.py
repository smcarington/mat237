# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-13 21:15
from __future__ import unicode_literals

import Problems.models
import Problems.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Problems', '0070_auto_20160806_1817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='expires',
            field=models.DateTimeField(blank=True, default=Problems.models.get_time, null=True),
        ),
        migrations.AlterField(
            model_name='linkeddocument',
            name='doc_file',
            field=models.FileField(upload_to=Problems.models.directory_setter, validators=[Problems.validators.FileValidator(content_types=('application/pdf', 'image/jpeg', 'image/png'))]),
        ),
        migrations.AlterUniqueTogether(
            name='studentvote',
            unique_together=set([]),
        ),
    ]
