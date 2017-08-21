from django_tables2 import tables, Column, Table

from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from django_tables2 import RequestConfig

from .models import *

class MathColumn(Column):
    # Records are MarkedQuestions
    def render(self, value, record):
        return format_html('<span class="mathrender">{}</span><br><small><a href="{}">(Edit)</a><a href="{}">(Delete)</a>', 
                mark_safe(value), 
                reverse('edit_quiz_question', 
                    kwargs={
                        'quiz_pk': record.quiz.pk,
                        'mq_pk': record.pk,
                    }
                ),
                reverse('delete_item', kwargs={'objectStr':'markedquestion', 'pk': record.pk}),
           )

#class LinkColumn(Column):
#    def render(self, record, value):
##        return format_html('<a href="{}">Edit Choices</a>', reverse('edit_choices', args=('1',)))
#        return format_html('{}', args=(record.id,))

class MarkedQuestionTable(Table):
    # Record is a MarkedQuestion
    problem_str = MathColumn()
    choices = Column(empty_values=())
    test = Column(empty_values=())
    class Meta:
        attrs = {'class': 'paleblue'}
        model = MarkedQuestion
        fields = ['category', 'problem_str', 'choices']

    def render_choices(self, value, record):
        return format_html('<a href={}>Edit Choices</a>', 
                reverse('edit_choices', 
                    kwargs={ 
                        'mq_pk': record.pk,
                        'quiz_pk': record.quiz.pk,
                    }
                ) 
            )

    def render_test(self,value,record):
        return format_html('<a href={}>Test</a>', 
                reverse('test_quiz_question', 
                    kwargs={
                        'mq_pk':record.pk,
                        'quiz_pk': record.quiz.pk,
                    }
                ) 
            )

class AllQuizTable(Table):
    out_of = Column("Points", empty_values=())

    class Meta:
        model = Quiz
        attrs = {'class': 'paleblue'}
        exclude = ['id', '_cat_list']

    def render_out_of(self, value, record):
        return record.out_of

    def render_cat_list(self, value, record):
        return len(cat_list)

    def render_tries(self, value, record):
        # Returns the value or infinity if value is 0
        return value or format_html('&infin;')

    def render_name(self, value, record):
        return format_html('<a href={}>{}</a>', 
            reverse('quiz_admin', 
                kwargs={'quiz_pk': record.pk,}
            ), value 
        )

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

def html_for_notes(notes):
    """ Subroutine for returning the html strings for notes, whether
        accepted or not. Used in both render_score and render_percent. 
        Input: Array of [StudentDocument]
        Output: HTML string
    """
    if [note for note in notes if note.accepted]:
        return format_html('<span>{}</span>', "Exempt")
    else:
        return format_html('<span>{}</span>', "Submitted")

class MarksTable(Table):
    """ Used for displaying a student's individual marks. The score and percent
        will render differently if a note has been submitted for this work.
        `record' will therefore be a StudentMark object
    """
    name    = Column(verbose_name="Name", empty_values=())
    out_of  = Column(verbose_name="Out of", empty_values=())
    score   = Column(verbose_name="Score", empty_values=())
    percent = Column(verbose_name="Percent", empty_values=())

    class Meta:
        attrs = {'class': 'paleblue'}

    def render_name(self, value, record):
        return record.category.name

    def render_out_of(self, value, record):
        return str(record.category.out_of)

    def render_score(self, value, record):
        notes = record.has_note()
        if notes: 
            return html_for_notes(notes)
        else:
            return value

    def render_percent(self, value, record):
        notes = record.has_note()
        if notes:
            return html_for_notes(notes)
        else:
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
        row_attrs = {'data-active': lambda record: record.user.is_active}

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
        row_attrs = {'data-active': lambda record: record.user.is_active}

def define_all_marks_table():
    """ A helper function which extends the base SeeAllMarksTable for variable category types.
        Input: categories (List of Evaluation) - Add these as columns to the table
        Return: (SeeAllMarksTable, Table) object
    """
    
    categories = Evaluation.objects.all().order_by('name')
    attrs = dict( (cat.name.replace(' ', ''), Column(verbose_name=cat.name)) for cat in categories)
    # Meta is not inherited, so need to explicitly define it
    attrs['Meta'] = type('Meta', 
                         (), 
                         dict(attrs={"class":"paleblue", "orderable":"True"}, 
                              order_by=("last_name","first_name",)
                              )
                         )
    dyntable = type('FullMarksTable', (SeeAllMarksTable,), attrs)

    return dyntable

class CSVPreviewTable(Table):
    student_number = Column(verbose_name="Student Number")
    grade          = Column(verbose_name="Grade")

    class Meta:
        attrs = {'class': 'paleblue'}
        order_by = 'student_number'

    def render_student_number(self, value, record):
        try:
            int(value)
            return value
        except:
            return format_html('<span style="color:red">{}</span>', value)

    def render_grade(self, value, record):
        try:
            float(value)
            return value
        except:
            return format_html('<span style="color:red">{}</span>', value)
