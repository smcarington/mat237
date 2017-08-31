# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-25 15:42
from __future__ import unicode_literals

import Problems.models
import Problems.validators
from django.conf import settings
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=30)),
                ('text', models.TextField()),
                ('stickied', models.BooleanField(default=False)),
                ('created_date', models.DateTimeField(default=Problems.models.get_localtime)),
                ('published_date', models.DateTimeField(blank=True, null=True)),
                ('expires', models.DateTimeField(blank=True, default=Problems.models.get_time, null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CSVBackup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_file', models.FileField(upload_to=Problems.models.directory_setter, validators=[Problems.validators.FileValidator(content_types=('application/pdf', 'image/jpeg', 'image/png', 'text/plain'))])),
                ('file_name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DocumentCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cat_name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Evaluation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('out_of', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='LinkedDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_file', models.FileField(upload_to=Problems.models.directory_setter, validators=[Problems.validators.FileValidator(content_types=('application/pdf', 'image/jpeg', 'image/png', 'text/plain'))])),
                ('link_name', models.CharField(max_length=200)),
                ('live_on', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='docs', to='Problems.DocumentCategory')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problems_linkeddocument_related', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MarkedQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.IntegerField(default=1, verbose_name='Category')),
                ('problem_str', models.TextField(verbose_name='Problem')),
                ('choices', models.TextField(null=True, verbose_name='Choices')),
                ('num_vars', models.IntegerField(null=True)),
                ('answer', models.TextField(verbose_name='Answer')),
                ('functions', models.TextField(default='{}', verbose_name='Functions')),
                ('q_type', models.CharField(choices=[('D', 'Direct Entry'), ('MC', 'Multiple Choice'), ('TF', 'True/False')], default='D', max_length=2, verbose_name='Question Type')),
                ('mc_choices', models.TextField(blank=True, default='[]', verbose_name='Multiple Choice')),
            ],
            options={
                'verbose_name': 'Marked Question',
                'ordering': ['quiz', 'category'],
            },
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='PollChoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=400)),
                ('num_votes', models.IntegerField(default=0)),
                ('cur_poll', models.IntegerField(default=1)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='PollQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(blank=True)),
                ('live', models.BooleanField(default=False)),
                ('num_poll', models.IntegerField(default=1)),
                ('visible', models.BooleanField(default=False)),
                ('can_vote', models.BooleanField(default=False)),
                ('position', models.IntegerField(default=0)),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Problems.Poll')),
            ],
        ),
        migrations.CreateModel(
            name='ProblemSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=20)),
                ('visible', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('difficulty', models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard'), (4, 'Impossible')], default=1)),
                ('attempts', models.IntegerField(default=0)),
                ('solved', models.IntegerField(default=0)),
                ('stud_diff', models.IntegerField(default=1)),
                ('solution', models.TextField(blank=True, default='')),
                ('problem_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problems', to='Problems.ProblemSet')),
            ],
        ),
        migrations.CreateModel(
            name='QuestionStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt', models.BooleanField(default=False)),
                ('solved', models.BooleanField(default=False)),
                ('difficulty', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)], default=1)),
                ('solution', models.TextField(default='')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status', to='Problems.Question')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_status', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('tries', models.IntegerField(default=0, verbose_name='Tries')),
                ('live', models.DateTimeField(verbose_name='Live on')),
                ('expires', models.DateTimeField(verbose_name='Expires on')),
                ('_cat_list', models.TextField(null=True)),
            ],
            options={
                'verbose_name': 'Quiz',
                'verbose_name_plural': 'Quizzes',
            },
        ),
        migrations.CreateModel(
            name='StudentDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_file', models.FileField(storage=django.core.files.storage.FileSystemStorage(location='/stud/cslec/tholden/website/notes/sick_notes'), upload_to=Problems.models.note_name_setter, validators=[Problems.validators.FileValidator(content_types=('application/pdf', 'image/jpeg', 'image/png'), max_size=1024000)])),
                ('uploaded', models.DateTimeField(default=django.utils.timezone.now)),
                ('accepted', models.BooleanField(default=False)),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Problems.Evaluation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StudentInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_number', models.CharField(max_length=20)),
                ('lecture', models.CharField(max_length=20, null=True)),
            ],
            options={
                'ordering': ['user', 'student_number', 'lecture', 'tutorial'],
            },
        ),
        migrations.CreateModel(
            name='StudentMark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(blank=True, null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Problems.Evaluation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__username', 'category'],
            },
        ),
        migrations.CreateModel(
            name='StudentQuizResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt', models.IntegerField(default=1, null=True)),
                ('cur_quest', models.IntegerField(default=1, null=True)),
                ('result', models.TextField(default='{}')),
                ('score', models.IntegerField(null=True)),
                ('_q_order', models.TextField(default='')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Problems.Quiz')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Quiz Result',
            },
        ),
        migrations.CreateModel(
            name='StudentVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cur_poll', models.IntegerField(default=1)),
                ('question', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Problems.PollQuestion')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('vote', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='Problems.PollChoice')),
            ],
        ),
        migrations.CreateModel(
            name='Tutorial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('max_enrol', models.IntegerField()),
                ('cur_enrol', models.IntegerField()),
                ('add_info', models.TextField(blank=True, null=True)),
                ('ta', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Typo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document', models.CharField(choices=[('Mat134', 'Mat 134'), ('Mat237', 'Mat 237')], max_length=100)),
                ('page', models.IntegerField()),
                ('description', models.TextField()),
                ('verified', models.BooleanField(default=False)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='studentinfo',
            name='tutorial',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='students', to='Problems.Tutorial'),
        ),
        migrations.AddField(
            model_name='studentinfo',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='info', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pollchoice',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Problems.PollQuestion'),
        ),
        migrations.AddField(
            model_name='markedquestion',
            name='quiz',
            field=models.ForeignKey(null=True, on_delete=Problems.models.Quiz, to='Problems.Quiz'),
        ),
        migrations.AddField(
            model_name='csvbackup',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Problems.Evaluation'),
        ),
        migrations.AddField(
            model_name='csvbackup',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problems_csvbackup_related', to=settings.AUTH_USER_MODEL),
        ),
    ]
