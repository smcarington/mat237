from django import template
from Problems.models import ProblemSet
from django.core.urlresolvers import resolve, Resolver404

register = template.Library()

@register.inclusion_tag('Problems/navbar_inclusion_tag.html', takes_context = True)
def navbar_inclusion_tag(context):
    ps_titles = ProblemSet.objects.all().values_list('title', flat=True)
    return {'problem_sets': ps_titles, 'request': context.request }

@register.simple_tag
def check_active(request, view_name):
    if not request:
        return ''
    try:
        return 'active' if resolve(request.path_info).url_name == view_name else ""
    except Resolver404:
        return ''
