from django_tables2 import tables, Column, Table

from django.utils.html import format_html
from django.core.urlresolvers import reverse

from .models import MarkedQuestion, Quiz, StudentQuizResult, StudentDocument, StudentMark

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
    test = Column(empty_values=())
    class Meta:
        attrs = {'class': 'paleblue'}
        model = MarkedQuestion
        fields = ['category', 'problem_str', 'choices']

    def render_choices(self, value, record):
        return format_html('<a href={}>Edit Choices</a>', reverse('edit_choices', args=(record.pk,)) )

    def render_test(self,value,record):
        return format_html('<a href={}>Test</a>', reverse('test_quiz_question', args=(record.pk,)) )

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
    details   = Column("Details", empty_values=(), orderable=False)

    class Meta:
        model = StudentQuizResult
        attrs = {'class': 'paleblue'}
        fields = ['quiz', 'attempt', 'cur_quest', 'score']

    def render_cur_quest(self, value, record):
        if value == 0:
            return "Completed"
        else:
            return value

    def render_details(self, value, record):
        return format_html('<a href="{}">Details</a>', reverse('quiz_details', args=(record.pk,)))

class QuizResultTable(Table):
    q_num   = Column(verbose_name="Question")
    correct = Column(verbose_name="Correct Answer")
    guess   = Column(verbose_name="Your Answer")
    score   = Column(verbose_name="Score")

    class Meta:
        attrs = {'class': 'paleblue'}
        order_by = 'q_num'

class NotesTable(Table):
    exemption = Column(verbose_name="Exemption")
    uploaded  = Column(verbose_name="Uploaded")
    accepted  = Column(verbose_name="Accepted")
    preview   = Column(verbose_name="Preview",empty_values=())

    class Meta:
        model = StudentDocument
        attrs = {'class': 'paleblue'}
        exclude = ['user', 'id', 'doc_file']

    def render_preview(self, value, record):
        return format_html('<a href={}>Click to Preview</a>', reverse('get_note', args=(record.doc_file.name,)))

class MarksTable(Table):
    name    = Column(verbose_name="Name", empty_values=())
    score   = Column(verbose_name="Score", empty_values=())
    out_of  = Column(verbose_name="Out of", empty_values=())
    percent = Column(verbose_name="Percent", empty_values=())

    class Meta:
        attrs = {'class': 'paleblue'}

    def render_name(self, value, record):
        return record.category.name

    def render_out_of(self, value, record):
        return str(record.category.out_of)

    def render_percent(self, value, record):
        return str(round(100*record.score/record.category.out_of,2))

class MarkSubmitTable(Table):
    last_name  = Column(verbose_name="First Name", accessor='sm.user.last_name')
    first_name = Column(verbose_name="Name", accessor='sm.user.first_name')
    username   = Column(verbose_name="UTORid", accessor='sm.user.username')
    number     = Column(verbose_name="Student Number", accessor='sm.user.info.student_number')


    class Meta:
        model = StudentMark
        attrs = {'class': 'paleblue'}

    def render_name(self, value, record):
        return record.category.name

    def render_out_of(self, value, record):
        return str(record.category.out_of)

    def render_percent(self, value, record):
        return str(round(100*record.score/record.category.out_of,2))
