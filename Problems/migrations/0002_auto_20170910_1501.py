# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-10 19:01
from __future__ import unicode_literals

import Problems.models
import Problems.validators
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Problems', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='immediate_solutions',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='studentdocument',
            name='doc_file',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(location='/tmp/note'), upload_to=Problems.models.note_name_setter, validators=[Problems.validators.FileValidator(content_types=('application/pdf', 'image/jpeg', 'image/png'), max_size=1024000)]),
        ),
        migrations.AlterField(
            model_name='tutorial',
            name='cur_enrol',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='tutorial',
            name='max_enrol',
            field=models.IntegerField(default=40),
        ),
    ]
