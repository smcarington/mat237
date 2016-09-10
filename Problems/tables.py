from django_tables2 import tables, Column, Table

from django.utils.html import format_html
from django.core.urlresolvers import reverse

from .models import MarkedQuestion, Quiz, StudentQuizResult, StudentDocument, StudentMark, ExemptionType

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

    def render_correct(self, value, record):
        return format_html('<span class="diff">{}</span>', value)

    def render_guess(self, value, record):
        return format_html('<span class="diff">{}</span>', value)

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
        if record.score:
            return str(round(100*record.score/record.category.out_of,2))
        else:
            return ''

class MarkSubmitTable(Table):
    last_name  = Column(verbose_name="First Name", accessor='user.last_name')
    first_name = Column(verbose_name="Last Name", accessor='user.first_name')
    username   = Column(verbose_name="UTORid", accessor='user.username')
    number     = Column(verbose_name="Student Number", accessor='user.info.student_number')
    score      = Column(verbose_name="Score", empty_values=())

    class Meta:
        attrs = {'class': 'paleblue'}

    def render_score(self, value, record):
        template = "<input name='user_{userpk}' data-category='{category}' data-user='{userpk}' value='{score}' size='10'>"
        if record.score is None:
            score = ''
        else:
            score = record.score
        return format_html(template, userpk=record.user.pk, category=record.category.pk, score=score)

class SeeAllMarksTable(Table):
    last_name  = Column(verbose_name="Last Name")
    first_name = Column(verbose_name="First Name")
    username   = Column(verbose_name="UTORid")
    number     = Column(verbose_name="Student Number")

    class Meta:
        attrs = {'class': 'paleblue'}

def define_all_marks_table():
    """ A helper function which extends the base SeeAllMarksTable for variable category types.
        Input: categories (List of ExemptionType) - Add these as columns to the table
        Return: (SeeAllMarksTable, Table) object
    """
    
    categories = ExemptionType.objects.all()
    attrs = dict( (cat.name.replace(' ', ''), Column(verbose_name=cat.name)) for cat in categories)
    # Meta is not inherited, so need to explicitly define it
    attrs['Meta'] = type('Meta', (), dict(attrs={"class":"paleblue", "orderable":"True"}, order_by=("last_name","first_name",)))
    dyntable = type('FullMarksTable', (SeeAllMarksTable,), attrs)

    return dyntable
