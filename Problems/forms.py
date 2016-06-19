from django import forms
from .models import Announcement, Question, ProblemSet, Poll, PollQuestion, PollChoice, LinkedDocument
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

class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ('title',)

class LinkedDocumentForm(forms.ModelForm):
    class Meta:
        model  = LinkedDocument
        fields = ('link_name', 'doc_file', 'category')

class TextFieldForm(forms.Form):
    attrs = {'cols': '150', 'rows': '30'}
    text_field = forms.CharField(widget=forms.Textarea(attrs))
