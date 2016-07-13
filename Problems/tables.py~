from django_tables2 import tables, Column, Table

from django.utils.html import format_html
from django.core.urlresolvers import reverse

from .models import MarkedQuestion, Quiz, StudentQuizResult

class MathColumn(Column):
    def render(self, value, record):
        return format_html('<span class="diff">{}</span><small><a href="{}">(Edit)</a>', 
                value, 
                reverse('edit_quiz_question', args=(record.quiz.pk, record.pk,))
               )

#class LinkColumn(Column):
#    def render(self, record, value):
##        return format_html('<a href="{}">Edit Choices</a>', reverse('edit_choices', args=('1',)))
#        return format_html('{}', args=(record.id,))

class MarkedQuestionTable(Table):
    problem_str = MathColumn()
    choices = Column(empty_values=())
    class Meta:
        attrs = {'class': 'paleblue'}
        model = MarkedQuestion
        fields = ['category', 'problem_str', 'choices']

    def render_choices(self, value, record):
        return format_html('<a href={}>Edit Choices</a>', reverse('edit_choices', args=(record.pk,)) )

class AllQuizTable(Table):
    class Meta:
        model = Quiz
        attrs = {'class': 'paleblue'}
        exclude = ['id']

    def render_name(self, value, record):
        return format_html('<a href={}>{}</a>', reverse('quiz_admin', args=(record.pk,)), value )

class SQRTable(Table):
    quiz      = Column("Quiz")
    attempt   = Column("Attempt")
    cur_quest = Column("Question")
    score     = Column("Score")
    class Meta:
        model = StudentQuizResult
        attrs = {'class': 'paleblue'}
        fields = ['quiz', 'attempt', 'cur_quest', 'score']

    def render_cur_quest(self, value, record):
        if value == 0:
            return "Completed"
        else:
            return value


class QuizResultTable(Table):
    q_num   = Column(verbose_name="Question")
    correct = Column(verbose_name="Correct Answer")
    guess   = Column(verbose_name="Your Answer")
    score   = Column(verbose_name="Score")

    class Meta:
        attrs = {'class': 'paleblue'}
