from django import forms
from .models import Announcement, Question, ProblemSet
from django.contrib.admin import widgets

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('title', 'text', 'stickied', 'expires')
        help_texts = {
            'text': 'Format using HTML.',
            'expires': 'Default is 3 weeks',
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('difficulty', 'text')

class ProblemSetForm(forms.ModelForm):
    class Meta:
        model = ProblemSet
        fields = ('title',)

class NewStudentUserForm(forms.Form):
    username = forms.CharField(label='username', max_length=20)
    email    = forms.CharField(label='email', max_length=100)
