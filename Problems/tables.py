from django_tables2 import tables, Column

from django.utils.html import format_html
from django.core.urlresolvers import reverse

from .models import MarkedQuestion

class MathColumn(Column):
    def render(self, value):
        return format_html('<span class="diff">{}</span>', value)

class LinkColumn(Column):
    def render(self, value):
        return format_html('<a href="{}">Edit Choices</a>', reverse('edit_choices', args=(value.pk,)))

class MarkedQuestionTable(tables.Table):
    problem_str = MathColumn()
    choices = LinkColumn()
    class Meta:
        attrs = {'class': 'paleblue'}
        model = MarkedQuestion
        fields = ['category', 'problem_str', 'choices']
