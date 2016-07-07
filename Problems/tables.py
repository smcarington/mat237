from django_tables2 import tables
from .models import MarkedQuestion

class MarkedQuestionTable(tables.Table):
    class Meta:
        attrs = {'class': 'paleblue'}
        model = MarkedQuestion
        fields = ['category', 'problem_str']
