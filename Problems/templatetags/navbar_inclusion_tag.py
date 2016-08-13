from django import template
from Problems.models import ProblemSet, PollQuestion, PollChoice
from django.core.urlresolvers import resolve, Resolver404
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.conf import settings

import re

register = template.Library()

@register.inclusion_tag('Problems/navbar_inclusion_tag.html', takes_context = True)
def navbar_inclusion_tag(context):
    ps = ProblemSet.objects.all().order_by('pk')
    return {'problem_sets': ps, 
            'request': context.request, 
            'site_name': settings.SITE_NAME,
            'logout_page': settings.LOGOUT_REDIRECT_URL}

@register.simple_tag
def check_active(request, view_name):
    if not request:
        return ''
    try:
        if view_name in resolve(request.path_info).url_name:
            return 'active'
        else:
            return ''
    except Resolver404:
        return ''

@register.filter
def num2diff(value):
    # Takes a number {1,2,3,4} and returns {easy,med,hard,imp}
    if value == 1:
        return "Easy"
    elif value == 2:
        return "Medium"
    elif value == 3:
        return "Hard"
    elif value == 4:
        return "Bonus"
    else:
        return ""

@register.simple_tag
def to_percent(num, den):
    return round(100*num/den)

@register.simple_tag
def score_div(num, den):
    div_str = '<div class="{cl}" style="width: {widthperc}%; margin-left:30px">{perc}% <small>({num_votes} votes)</small></div>'

    if den == 0:
        ret_str = div_str.format(cl="zerobar", widthperc=100, perc="No votes", num_votes="No")
    else:
        percent = round(100*num/den)
        if percent==0:
            ret_str = div_str.format(cl="zerobar", widthperc=100, perc=percent, num_votes=num)
        else:
            ret_str = div_str.format(cl="bar", widthperc=percent, perc=percent, num_votes=num)

    return mark_safe(ret_str)

@register.simple_tag
def total_votes(questionpk, cur_poll):
    # For the question with pk questionpk, and the choices with cur_poll, return the total votes
    q = PollQuestion.objects.get(pk=questionpk)
    choices = q.pollchoice_set.filter(cur_poll=cur_poll)
    return sum(choices.values_list('num_votes', flat=True))

@register.simple_tag
def mathify_choice(choice):
    """ Takes a choice list from a MarkedQuestion element and outputs the math friendly html. Currently only
        supports integers.
        Input: choice (list of strings) -
        Output: KaTeX renderable HTML.
    """
    mathstring = '\(\{'
    for element in choice.replace(' ', '').split(';'):
        if is_integer(element):
            mathstring += element + ','
        else:
            try:
                match1 = re.match(r'rand\((-?\d+),(-?\d+)\)',element)
                match2 = re.match(r'uni\((-?\d+),(-?\d+),(\d+)\)',element)

                if match1:
                    field = '\mathbb Z'
                    lower,upper = match1.groups(0)
                    acc = ''
                elif match2:
                    field = '\mathbb R'
                    lower,upper,acc = match2.groups(0)

            #    lower,upper = element[1:].split(',')
            #    integer = '\mathbb Z'

            #    if element[0].istitle():
            #        integer +='^*'

                mathstring += ' {field}_{{ {acc} }}({low},{upp}), '.format(field=field, low=lower, upp=upper, acc=acc)

            except ValueError as error:
                print(error)
                return ''

    # Remove the final unnecessary ','
    mathstring = mathstring[0:-1]
    mathstring += '\}\)'

    return format_html('<label class="diff">{}</label>', mathstring)

def is_integer(string):
    try:
        int(string)
        return True
    except ValueError:
        return False;

@register.filter
def filter_poll_choice(query_set, poll=None):
    if type(query_set) is PollQuestion:
        if poll is None:
            return query_set.pollchoice_set.filter(cur_poll=query_set.num_poll).order_by('id')
        else:
            return query_set.pollchoice_set.filter(cur_poll=poll).order_by('id')
    elif type(query_set) is PollChoice:
        return query_set.filter(cur_poll=poll)

@register.filter
def get_range(value):
    "Generates a range for numeric for loops"
    return range(value)

