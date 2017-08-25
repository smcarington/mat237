# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-25 14:09
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
        migrations.AlterField(
            model_name='studentdocument',
            name='doc_file',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(location='/stud/cslec/tholden/website/notes/sick_notes'), upload_to=Problems.models.note_name_setter, validators=[Problems.validators.FileValidator(content_types=('application/pdf', 'image/jpeg', 'image/png'), max_size=1024000)]),
        ),
    ]
