from django import forms
from django.forms import IntegerField
from django.db.models import F
from .models import (Announcement, Question, ProblemSet, Poll, PollQuestion,
PollChoice, LinkedDocument, Quiz, MarkedQuestion, StudentDocument,
ExemptionType, DocumentCategory, Typo, Tutorial, CSVBackup)
from django.contrib.admin import widgets

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('title', 'text', 'stickied', 'expires')
        help_texts = {
            'text': 'Format using HTML.',
            'expires': 'Default is 1 week.',
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('difficulty', 'text', 'solution')
        widgets = {
            'solution': forms.Textarea({'style':'width: 100%'}),
        }

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
        fields = ('link_name', 'doc_file', 'category', 'live_on')

class TextFieldForm(forms.Form):
    attrs = {'cols': '150', 'rows': '30'}
    text_field = forms.CharField(widget=forms.Textarea(attrs))

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        exclude = ['out_of']

class StudentDocumentForm(forms.ModelForm):
    class Meta:
        model = StudentDocument
        exclude = ['user', 'accepted', 'uploaded']

class CSVBackupForm(forms.ModelForm):
    """ Model form for CSVBackup. Since it needs to be used both for updating
        marks and setting active students, we may not want a `category' to be
        assigned. Hence we override the constructor the include a conditional
        'include_cat' which when set to true include the category in the form.
    """

    def __init__(self, *args, **kwargs):
        include_cat = kwargs.pop('include_cat', True)
        super(CSVBackupForm, self).__init__(*args, **kwargs)

        if not include_cat:
            del self.fields['category']

    class Meta:
        model = CSVBackup
        fields = ['doc_file', 'category']

class MarkedQuestionForm(forms.ModelForm):
#    category = IntegerField(min_value=1, initial=1)
#
#    problem_str = forms.CharField(widget=forms.Textarea(text_area_attrs))

    class Meta:
        text_area_attrs = {'cols':'80', 'rows': '5'}
        mc_attrs = dict(text_area_attrs, **{'visible': 'false'})
        model = MarkedQuestion
        fields = ['category', 'problem_str', 'answer', 'q_type', 'mc_choices', 'functions']
        help_texts = {
            'problem_str': 'Use {v[0]}, {v[1]}, ... to indicate variables.',
            'category': 'Used to group several questions into the same category for randomization',
            'answer': 'Use the same variables as in problem. Use python calculate the answer.<br> For example, myfun({v[0]},{v[1]}).',
            'functions': 'Define custom functions using a dictionary. For example, {"myfun": lambda x,y: max(x,y)}.<br>'
                         'Your answer must contain all variables. The "gobble" function returns 1, and can be used as such.',
            'mc_choices': 'Enter a list with possible values, seperated by a semi-colon. For example, <code>None of the above; 15*{v[0]}; At most \(@2*{v[0]}@\)</code>. Any functions '
                          'you define can be used here, for example {"rand": lambda x: math.randint(1,10)}',
        }
        labels = {
            'problem_str': 'Problem',
            'category': 'Category',
        }
        widgets = {
            'problem_str': forms.Textarea(text_area_attrs),
            'answer': forms.Textarea(text_area_attrs),
            'functions': forms.Textarea(text_area_attrs),
            'mc_choices': forms.Textarea(mc_attrs),
        }
        field_classes = {
            'category': forms.IntegerField
        }

class ExemptionForm(forms.ModelForm):
    class Meta:
        model = ExemptionType
        fields = ('name','out_of')

class CategoryForm(forms.ModelForm):
    class Meta:
        model = DocumentCategory 
        fields = ('cat_name',)

class TypoForm(forms.ModelForm):
    attrs = {'cols': '100', 'rows': '10'}
    description = forms.CharField(widget=forms.Textarea(attrs))
    class Meta:
        model = Typo
        exclude = ('user','verified',)

class PopulateCategoryForm(forms.Form):
    exemption = forms.ModelMultipleChoiceField(queryset=ExemptionType.objects.all())

class ChangeTutorialForm(forms.Form):
    tutorial = forms.ModelChoiceField(queryset=Tutorial.objects.filter(cur_enrol__lt=F('max_enrol')))

    class Meta:
        help_text = {
            'tutorial': "Select your tutorial. If a tutorial is not visible, "
                        "is at full capacity.",
        }
