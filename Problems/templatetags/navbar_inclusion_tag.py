from django import template
from Problems.models import ProblemSet

register = template.Library()

@register.inclusion_tag('Problems/navbar_inclusion_tag.html')
def navbar_inclusion_tag():
    ps_titles = ProblemSet.objects.all().values_list('title', flat=True)
    return {'problem_sets': ps_titles }

