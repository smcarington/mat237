from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.html import mark_safe, format_html
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.views import password_change
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail, EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.core.files import File
from django.conf import settings
from django.db.models import Max, Q, F
from django.db import IntegrityError

from django_tables2 import RequestConfig

import json
import subprocess
import os
import re
import itertools
import math
import csv #Used for updating marks from a csv file
import logging
from operator import attrgetter
from sendfile import sendfile

from django.contrib.auth.models import User
from .models import Announcement, ProblemSet, Question, QuestionStatus, Poll, PollQuestion, PollChoice, LinkedDocument, StudentVote, StudentDocument, Typo, StudentMark, StudentInfo
from .forms import *
import random
import math
from simpleeval import simple_eval, NameNotDefined

from django.contrib.auth.models import User
from .models import Announcement, ProblemSet, Question, QuestionStatus, Poll, PollQuestion, PollChoice, LinkedDocument, Quiz, MarkedQuestion, StudentQuizResult, Evaluation
from .forms import (AnnouncementForm, QuestionForm, ProblemSetForm,
        NewStudentUserForm, PollForm, LinkedDocumentForm, TextFieldForm,
        QuizForm, MarkedQuestionForm, CSVBackupForm)
from .tables import (MarkedQuestionTable, AllQuizTable, QuizResultTable,
        SQRTable, NotesTable, MarksTable, MarkSubmitTable, define_all_marks_table,
        CSVPreviewTable)

# Create your views here.

def staff_required(login_url=settings.LOGIN_URL):
    return user_passes_test(lambda u:u.is_staff, login_url=login_url)

# @login_required
def post_announcements(request):
    posts = Announcement.objects.filter(expires__gte=timezone.now()).order_by('-stickied', '-published_date')
    ajax_url = reverse('get_old_announcements')

    return render(request, 'Problems/post_announcements.html', 
        {'announcements': posts,
         'ajax_url': ajax_url,
        })

def get_old_announcements(request):
    posts = Announcement.objects.filter(expires__lt=timezone.now()).order_by('-stickied', '-published_date')
    return render(request, 'Problems/old_announcements.html', {'ann': posts})

@staff_required()
def new_announcement(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.publish()
            return redirect(post_announcements)
    else:
        form = AnnouncementForm()

    return render(request, 'Problems/edit_announcement.html', {'form' : form})

@staff_required()
def edit_announcement(request, pk):
    post = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.publish()
            return redirect(post_announcements)
    else:
        form = AnnouncementForm(instance=post)

    return render(request, 'Problems/edit_announcement.html', {'form' : form})
#
# Deletes either an item or a list, as given by the string object_type
# Checks to see if the user is allowed access
@staff_required()
def delete_item(request, objectStr, pk):
    if request.user.is_staff:
        # Depending on which item is set, we return different pages
        if objectStr == "announcement":
            theObj      = get_object_or_404(Announcement, pk = pk)
            return_View = redirect('/')
        elif objectStr == "question":
            theObj      = get_object_or_404(Question, pk = pk)
            return_View = redirect('list_problem_set', pk=theObj.problem_set.pk)
        elif objectStr == "pollquestion":
            theObj      = get_object_or_404(PollQuestion, pk = pk)
            return_View = redirect('poll_admin', pollpk=theObj.poll.pk)
        elif objectStr == "typo":
            theObj      = get_object_or_404(Typo, pk = pk)
            return_View = redirect('see_typos')
        elif objectStr == "markedquestion":
            theObj      = get_object_or_404(MarkedQuestion, pk = pk)
            the_quiz    = theObj.quiz
            return_View = redirect('quiz_admin', quiz_pk=the_quiz.pk)
        else:
            return HttpResponse('<h1>Invalid Object Type</h1>')

        if request.method == "POST":
            theObj.delete()
            return return_View
        else:
            return render(request, 'Problems/delete_item.html', {'object': theObj, 'type' : objectStr})
    else:
        return HttpResponseForbidden()

@staff_required()
def new_question(request, listpk):
    if request.method == "POST":
        form = QuestionForm(request.POST)
        ps   = get_object_or_404(ProblemSet, pk=listpk)
        if form.is_valid():
            question = form.save(commit=False)
            question.problem_set = ps
            question.save()
            return redirect('list_problem_set', pk=listpk)
    else:
        form = QuestionForm()

    return render(request, 'Problems/edit_announcement.html', {'form' : form})

@staff_required()
def edit_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save(commit=False)
            question.save()
            return redirect('list_problem_set', pk=question.problem_set.pk)
    else:
        form = QuestionForm(instance=question)

    return render(request, 'Problems/edit_announcement.html', {'form' : form})

@staff_required()
def new_problem_set(request):
    if request.method == "POST":
        form = ProblemSetForm(request.POST)
        if form.is_valid():
            problem_set= form.save(commit=False)
            problem_set.save()
            return redirect('administrative')
    else:
        form = ProblemSetForm()

    return render(request, 'Problems/edit_announcement.html', {'form' : form})

@staff_required()
def post_delete(request, pk):
    post = get_object_or_404(Announcement, pk=pk)
    post.delete()
    return redirect('post_list')

def get_syllabus(new_text=None):
    """
        Helper function for syllabus and edit_syllabus views. Handles the actual
        file system for manipulating the syllabus
    """
    file_path = settings.MEDIA_ROOT + "/syllabus-body.txt"
    if new_text:
        try:
            with open(file_path, 'w') as f:
                f.write(new_text)
            return "Syllabus successfully updated"
        except Exception as e:
            raise e
    else:
        try:
            with open(file_path, 'r') as f:
                body = f.read()
            return body
        except Exception as e:
            raise e

def syllabus(request):
    body = get_syllabus()
    return render(request, 'Problems/syllabus.html', {'body': body} )

@staff_required()
def edit_syllabus(request):
    """
        Creates a form for editing the syllabus and updates that form
    """
    if request.method == "POST":
        new_text = request.POST['text_field']
        success_string  = get_syllabus(new_text)
        redirect_string = '<a href="{url}">Visit Syllabus Page</a>'.format(url=reverse('syllabus'))
        return render(request, 'Problems/success.html', {'success_string': success_string, 'redirect_string': redirect_string})
    else:
        cur_text = get_syllabus()
        data     = {'text_field': cur_text}
        form     = TextFieldForm(data)
        return render(request, 'Problems/edit_announcement.html', {'form' : form})

@login_required
def calendar(request):
    cal_source = mark_safe(settings.CALENDAR_SOURCE)
    return render(request, 'Problems/calendar.html',
        {'cal_source': cal_source,
        })

@login_required
def notes(request, page_number=''):
    # Post links in the sidebar. If user is staff, show unavailable links as
    # well
    if request.user.is_staff:
        docs = (LinkedDocument.objects.all().order_by('category', 'id'))
    else:
        docs = (LinkedDocument.objects.filter(live_on__lte=timezone.now())
                .order_by('category', 'id'))
    cat_names = DocumentCategory.objects.all().values_list('cat_name',
            flat=True) 
#    cat_names = docs.values_list('category__cat_name', flat=True).distinct()

    link_url = settings.NOTES_URL + '#'+ page_number

    return render(request, 'Problems/notes.html', 
            {'docs':docs, 
             'cats':cat_names,
             'ajax_url': settings.AJAX_TYPOS_URL,
             'link_url': link_url})

@login_required
def administrative(request):
        return render(request, 'Problems/administrative.html')

# --------- Problem Sets and Questions (fold) --------- #

@login_required
def list_problem_set(request, pk):
    """ Finds the problems corresponding to the given problem set and displays them.
        Input: (pk) The problem set primary key
    """
    ps = get_object_or_404(ProblemSet, pk=pk)

    # Ensure that if the problem set is not visible, students cannot see it
    if not ps.visible and not request.user.is_staff:
        raise Http404()

    # There is no standary sort_by on the charfield that returns difficulty, so we use the 'extra' method
    #CASE_SQL = '(case when difficulty="E" then 1 when difficulty="M" then 2 when difficulty="H" then 3 when difficulty="I" then 4 end)'
    #problems = ps.problems.extra(select={'difficulty': CASE_SQL}, order_by=['difficulty'])
    problems = ps.problems.order_by('difficulty', 'pk')
    ajax_url = reverse('pdflatex')

    return render(request, 'Problems/list_problem_set.html', 
        {   'problems': problems, 
            'problem_set': ps,
            'ajax_url': ajax_url,
        })

@csrf_protect
@login_required
def question_details(request, pk):
    problem = get_object_or_404(Question, pk=pk)
    problemStatus, created = QuestionStatus.objects.get_or_create(user=request.user, question=problem)

    if request.method == "POST":
        solution = request.POST['solution']
        problemStatus.solution = solution
        problemStatus.save()

    ajax_url = reverse('update_status')
    return render(request, 'Problems/question_details.html', 
        {'problem': problem, 
         'status': problemStatus,
         'ajax_url': ajax_url,
        })

@login_required
def question_solution(request, question_pk):
    problem = get_object_or_404(Question, pk=question_pk)

    return render(request, 'Problems/question_solution.html',
            {'problem': problem,
            })

@csrf_protect
@login_required
def update_status(request):
    try:
        user     = get_object_or_404(User, pk=int(request.POST['user']))
        question = get_object_or_404(Question, pk=int(request.POST['question']))
        status   = get_object_or_404(QuestionStatus, user=user, question=question)
    except:
        raise Http404('A variable was not correctly defined');

    response_data = {'response': ''}

    diff_int = int(request.POST['difficulty'])

    if diff_int > 10 or diff_int < 1:
        response_data['response'] = 'Must pass an integer between 1 and 10. Data not saved'
        return HttpResponse(json.dumps(response_data))

    if user == request.user:
        status.attempt    = (request.POST['attempted'].lower() == 'true')
        status.solved     = (request.POST['solved'].lower() == 'true')
        status.difficulty = diff_int
        status.save()
        response_data['response']='Status successfully updated!'
    else:
        return HttpResponseForbidden()

    return HttpResponse(json.dumps(response_data))

# --------- Problem Sets and Questions (end) --------- #

@staff_required()
def add_user(request):
# Create a new user, generate a random password, and email it
    if request.method == 'POST':
        form = NewStudentUserForm(request.POST)
        un = request.POST['username']
        em = request.POST['email']

        user  = User(username=un, email=em)
        rpass = User.objects.make_random_password()
        user.set_password(rpass)
        
        subject = "You have just been added to {site_name}".format(site_name=settings.SITE_NAME)
        message = """ You have just been added to the {site_name} course website, located at

{site_url}

Your username is {username} and your password is {password}. 
Please login and change your password
            """.format(username=un, password=rpass, site_name=settings.SITE_NAME, site_url = settings.SITE_URL)

        try:
            user.save()
            send_mail(subject, message, settings.DEFAULT_FROM_ADDRESS, [em])

            # Now send a confirmation to the staff member who added this user
            conf_subject = "User {student} has just been added to {site_name}".format(student=un, site_name=settings.SITE_NAME)
            conf_message = """The Student with the email address {email} and username {student} has been successfully added to the {site_name} group user list. No further action is required on your part.""".format(student=un, email=em, site_name=settings.SITE_NAME)

            send_mail(conf_subject, conf_message, settings.DEFAULT_FROM_ADDRESS, [request.user.email], fail_silently=False)
        except Exception as dbError:
            sidenote = "Error: Likely that a user with that username already exists"
            return render(request, 'Problems/edit_announcement.html', {'form' : form, "sidenote":sidenote})

        return redirect('administrative')
    else:
        form = NewStudentUserForm()

    return render(request, 'Problems/edit_announcement.html', {'form' : form})

@login_required
def polls(request):
    polls = Poll.objects.all()

    return render(request, 'Problems/list_polls.html', {'polls' : polls})

@staff_required()
def new_poll(request):
    if request.method == "POST":
        form = PollForm(request.POST)
        if form.is_valid():
            poll = form.save()
            return redirect('polls')
    else:
        form = PollForm()

    return render(request, 'Problems/edit_announcement.html', {'form' : form})

@login_required
def list_pollquestions(request, pollpk):
    poll = get_object_or_404(Poll, pk=pollpk)
    questions = poll.pollquestion_set.order_by('position')

    return render(request, 'Problems/list_pollquestions.html', {'questions': questions, 'poll': poll})

## ----------------- Poll Admin ----------------------- ##

# Only handles rendering the poll admin page. AJAX requests handled by other views
@staff_required()
def poll_admin(request, pollpk):
    poll = get_object_or_404(Poll, pk=pollpk)
    questions = poll.pollquestion_set.all().order_by('position')
    return render(request, 'Problems/poll_admin.html', {'poll': poll, 'questions': questions})

@staff_required()
def change_question_order(request):
    """ AJAX handler for poll_admin page to change question order. 
        request.POST should have elements action, pk
    """

    data   = request.POST
    pk     = int(data['pk'])
    action = data['action']

    question = get_object_or_404(PollQuestion, pk=pk)
    ret_flag = question.move_position(action)

    if (ret_flag < 0) :
        response_data = {'response': 'No movement of questions'}
    else:
        response_data = {'response': 'Question successfully moved'}

    return HttpResponse(json.dumps(response_data))

## ----------------- Poll Admin ----------------------- ##


@staff_required()
def new_pollquestion(request, pollpk, questionpk=None):
# To facilitate question + choice at the same time, we must instantiate the
# question before hand. This will also make editing a question easy in the
# future

    poll = get_object_or_404(Poll, pk=pollpk)

    # If a question is created for the first time, we must instantiate it so that
    # our choices have somewhere to point. If it already exists, retrieve it
    if questionpk is None:
        # With positioning, we need to determine the largest current position.
        cur_pos = PollQuestion.objects.filter(poll=poll).aggregate(Max('position'))

        if cur_pos['position__max'] is None:
            question = PollQuestion(poll=poll, position = 0)
        else:
            question = PollQuestion(poll=poll, position = cur_pos['position__max'] + 1)
        question.save()
    else:
        question = get_object_or_404(PollQuestion, pk=questionpk)

        if (request.method == "POST") and ('del' in request.POST):
            # User has left the page without submitting the form. So delete the question
            question.delete()
            data_response = {'response': 'Object successfully deleted'}
            return HttpResponse(json.dumps(data_response))

    if request.method == "POST":
        try:
            data = request.POST
            numChoices    = int(data['num-choice'])
            question.text = data['question']

            question.save()

            # Iterate through the choices. Ignore empty choices and otherwise create
            # database element. Note that numChoice is absolute (starts at 1), while 
            # the id's for input names start at 0
            for myit in range(0, numChoices):
                id_name = "new_" + str(myit)
                c_text = data[id_name]

                if c_text != '':
                    choice = PollChoice(question=question, text=c_text, cur_poll=question.num_poll)
                    choice.save()

            return redirect('poll_admin', pollpk=pollpk)
        except:
            raise Http404('Something went wrong!')

        return redirect('poll_admin', pollpk=pollpk)

    else:
        return render(request, 'Problems/new_pollquestion.html',  {'question' : question})

# Cannot just abuse new_question because we need to handle choices differently
@staff_required()
def edit_pollquestion(request, questionpk):
    question = get_object_or_404(PollQuestion, pk=questionpk)
    choices = question.pollchoice_set.filter(cur_poll=question.num_poll)

    # On form submission, update everything
    if request.method == "POST":
        form_data = request.POST
        # Note here that iteritems for python 2.x and items for python 3
        for field, data in form_data.items():
            if field == 'question':
                question.text = form_data[field]
                question.save()
            # 'old' indicates a previous existing choice
            elif 'old' in field:
                pkstring  = field.split('_')
                choice_pk = int(pkstring[-1])

                choice = get_object_or_404(PollChoice, pk=choice_pk)
                choice.text = form_data[field]
                if choice.text == '':
                    choice.delete()
                else:
                    choice.save()
            # 'choice' indicates a new choice that was added
            elif 'new' in field:
                c_text = form_data[field]

                choice = PollChoice(question=question, text=c_text, cur_poll=question.num_poll)
                choice.save()

        return redirect('poll_admin', pollpk=question.poll.pk)
    else:
        return render(request, 'Problems/new_pollquestion.html', {'question': question, 'choices': choices, 'edit': True})


# AJAX view for making a question live
@csrf_protect
def make_live(request):
    question = get_object_or_404(PollQuestion, pk=int(request.POST['question']))
    question.live = (request.POST['live']=='true');
    question.save()

    response_data = {'response': 'Question live: ' + str(question.live)}

    return HttpResponse(json.dumps(response_data))

# AJAX view for an administrator to start/stop/reset a question
@csrf_protect
def live_question(request):
    """
        AJAX view for poll-admin page. request.POST should have a field called 'status' which
        describes which button was hit. Can be one of
            'start'  - make a question live and open voting
            'stop'   - close voting, display results, and reset
            'endall' - removes questions from the poll page
    """
    if request.user.is_staff:
        data = request.POST
        question_pk = int(data['questionpk'])
        status   = data['action']

        if status == 'endall':
            PollQuestion.objects.filter(visible=True).update(visible=False, can_vote=False)
            response_data = {'response': 'Polling has ended'}
            return HttpResponse(json.dumps(response_data))
       
        question = get_object_or_404(PollQuestion, pk = question_pk)

        # The PollQuestion model has built in functions for this. But we have to make sure
        # that this is the only live question on start.
        #
        # As of June 15, 2015, moved reset() to stop.
        if status == 'start':
            # It is possible that the administrator accidentally hit the start button again.
            # We check to see if this is the case, and return an error message if so.
            if question.can_vote:
                response_data = {'response': 'This question is already active'}
            else: 
                # On 'start' we reset the poll. However, to avoid saving a bunch of empty polls
                # we first check to see if any votes have been cast.
                choices  = question.pollchoice_set.filter(cur_poll=question.num_poll)
                num_votes = sum(choices.values_list('num_votes', flat=True))

                response_data = {'response': 'Question pushed to live page'}
                if num_votes != 0:
                    pk_map = question.reset()
                    response_data['pkMap'] = pk_map

                PollQuestion.objects.filter(visible=True).update(visible=False, can_vote=False)
                question.start()
        elif status == 'stop':
            if not question.can_vote:
                response_data = {'response': 'This question is not live.'}
            elif not question.visible:
                response_data = {'response': 'That question is not visible'}
            else:
                question.stop()
                response_data = {'response': 'Question stopped. Displaying results.'}
#        elif status == 'reset':
#            if not question.visible:
#                response_data = {'response': 'That question is not visible'}
#            else:
#                pk_map = question.reset()
#                response_data = {'response': 'Data saved. Press start to reopen.', 'pkMap': pk_map}
    else:
        response_data = {'response': 'You are not authorized to make this POST'}

    return HttpResponse(json.dumps(response_data))

# Server is only ever in one of three states:
# 1. Nothing is happening
# 2. Question is displayed and voting
# 3. Question is display with results of most recent vote
# Depending on the states, we render a different page
@login_required
def live_poll(request):
    # See if a question has been opened by an administrator
    try: 
        question = PollQuestion.objects.get(visible=True)
        choices  = question.pollchoice_set.filter(cur_poll=question.num_poll)
        num_votes = sum(choices.values_list('num_votes', flat=True))

        state = str(question.pk)+"-"+str(question.can_vote)
        return render(request, 'Problems/live_poll.html', {'question': question, 'choices': choices, 'state': state, 'votes':num_votes})

    # If no question is currently live, we do nothing
    except PollQuestion.DoesNotExist:
        state = "-1"
        return render(request, 'Problems/live_poll.html', {'state': state})

@login_required
def query_live(request):
   
    # Votes are POSTed, status changes are done via GET
    # [Future] Currently user can vote as many times as they like by refreshing. May need
    # to create a db-model to track voting.
    if request.method == "POST":
        # POST will send choicepk as field 'pk'
        choicepk = int(request.POST['pk'])
        choice   = get_object_or_404(PollChoice, pk=choicepk)

        # Get or create a StudentVote object
        # In particular, check to see if the student has voted in the current poll.
        # Note that there is the potential here for race conditions
        try:
            svote, created = StudentVote.objects.get_or_create(student=request.user, cur_poll = choice.cur_poll, question=choice.question)
        except IntegrityError as dberror:
            return HttpResponse('<h2>You have attempted to submit multiple votes</h2>')

        if created: # First vote
            svote.choice = choice;
            svote.add_choice(choice)
        else: # Revoting, so change the vote
            if svote.vote != choice:
                svote.change_vote(choice)

        response_data = {'status': 'success'}
    else:
        try: 
            question = PollQuestion.objects.get(visible=True)
            state = str(question.pk)+"-"+str(question.can_vote)

            response_data = {'state': state}

            # If the user is staff, return the number of votes as well
            if request.user.is_staff:
                choices  = question.pollchoice_set.filter(cur_poll=question.num_poll)
                num_votes = sum(choices.values_list('num_votes', flat=True))
                response_data['numVotes'] = num_votes
                for choice in choices:
                    field = str(choice.pk)+"-votes"
                    num_votes = str(choice.num_votes)
                    response_data[field]=num_votes

        except Exception as e:
            response_data = {'state': "-1"}

    return HttpResponse(json.dumps(response_data))

## ----------------- PDFLATEX ----------------------- ## 

@login_required
def pdflatex(request):
    """ Accepts POST request from problem set page. Creates LaTeX document of the given files,
        sends them out to be compiled, then emails the pdf to the student.
    """

    if request.method == "POST":
        user = request.user
        data = json.loads(request.body.decode())

        problem_set = int(data['problem_set'])
        problemSet  = get_object_or_404(ProblemSet, pk=problem_set)
        questions   = data['questions']

        qlist = []

        # data should have a bunch of fields corresponding to the questions chosen
        
        # Student didnt select anything, just print all questions
        if len(questions) == 0:
            for question in problemSet.problems.all():
                qlist.append([question.text, '']) 
        else:
            for item in questions:
                qpk       = int(item['number'])
                
                # Grab the question, as well as the QuestionStatus object for that question
                # corresponding to the given user
                quest    = get_object_or_404(Question, pk=qpk)
                if item['sol']:
                    try:
                        sol_text = quest.status.get(user=user).solution
                    except QuestionStatus.DoesNotExist:
                        sol_text = ''
                else:
                    sol_text = ''

                text     = quest.text

                qlist.append([text, sol_text])

        # Send the data to a helper function to add the pre-amble. Returns a string which
        # we will make into a file for compiling
        ps_title = problemSet.title 
        latex_source = create_latex_source(qlist, ps_title)
        # Sanitize the string of html tags
        latex_source = latexify_string(latex_source)
        # Send the file to be compiled and emailed using another helper function
        response_data = compile_and_email(latex_source, user, str(problem_set))

        # return HttpResponse(json.dumps(response_data)) # from old email version

        return HttpResponse(reverse('get_ps', kwargs={'filename':response_data}))

    else:
        raise Http404('Request not posted')

@login_required
def get_ps(request, filename):
    user = request.user
        
    # Need to make sure students can only see their own files, or you are a staff member
    if (user.username in filename) or (user.is_staff):
        path = "/".join([settings.LATEX_ROOT, filename])
        return sendfile(request, path)
    else:
        return HttpResponseForbidden()
 

def latexify_string(string):
    """ A helper function which accepts a latex html string, possibly including tags,
        and returns a string where those tags have been appropriate replaced with
        LaTeX commands. For example, <ol>...</ol> will become \\begin{enumerate}...
        \\end{enumerate}
    """

    ret_string = string
    ret_string = re.sub(r'<ol.*?>', r'\t\\begin{enumerate}', ret_string)
    ret_string = re.sub(r'</ol>', r'\t\\end{enumerate}', ret_string)
    ret_string = re.sub(r'<ul.*?>', r'\t\\begin{itemize}', ret_string)
    ret_string = re.sub(r'</ul>', r'\t\\end{itemize}', ret_string)
    ret_string = re.sub(r'<li.*?>', r'\t\t\\item ', ret_string)
    ret_string = re.sub(r'(<br>)+', r'\\newline ', ret_string)
    ret_string = re.sub(r'<b.*?>(.*)</b>', r'\\textbf{\1}', ret_string)
    ret_string = re.sub(r'<i.*?>(.*)</i>', r'\\emph{\1}', ret_string)
    ret_string = re.sub(r'&lt;', r'<', ret_string)
    ret_string = re.sub(r'&gt;', r'>', ret_string)

    return ret_string

def create_latex_source(question_list, title):
    """ A helper function for the function 'pdflatex'. Accepts a list of questions and
        their solutions and assembles the appropriate latex file. 
        Input: question_list - a 2d array who's 0-argument is the question text and
                   whose 1-argument is the solution text (possibly empty)
        Out  : (string) with the full pdf source code
    """

    # Note that amssymb is the only package that we should need.
    preamble = """\\documentclass{{article}}
\\usepackage{{amssymb,amsthm, amsmath}}

\\newenvironment{{solution}}{{\\renewcommand\qedsymbol{{$\\blacksquare$}}
  \proof[Solution]
}}{{\\endproof}}

\\begin{{document}}
    \\begin{{center}} \\large {the_title} \\end{{center}}
    \\begin{{enumerate}}
""".format(the_title=title)
    postamb  = """
    \\end{enumerate}
\\end{document}"""
    temp_que = """    \\item {question_text}

"""
    temp_sol = """    
    \\begin{{solution}}
        {solution_text}
    \\end{{solution}}

"""
    document = preamble
    for question in question_list:
        document = document + temp_que.format(question_text=question[0])
        if question[1] !='':
            document = document + temp_sol.format(solution_text=question[1])

    return document + postamb

def compile_and_email(latex_source, user, ps_number):
    """ A helper function for the function 'pdflatex'. Accepts a string with the full latex
        source code. Creates a file with this string, compiles it, and emails it to the user.
        Input: latex_source - A (string) containing the latex source code.
               user         - (User) element corresponding to session user.
               ps_number    - (String) corresponding the problem set number
        Out  : A (string) indicating the success/failure of the method.
    """

    # Write the string to a file so that we can curl it to the external server
    # latex_directory = "/".join([settings.LATEX_ROOT, "latex"]) # old email
    user_specific_name = "latex_User-{userpk}_PS-{ps_number}.tex".format(userpk=user.username, ps_number=ps_number)
    file_name = "/".join([settings.LATEX_ROOT, user_specific_name])

    with open(file_name, 'w') as f:
        f.write(latex_source)
    
    command = ["pdflatex", "-halt-on-error", "-output-directory={dir}".format(dir=settings.LATEX_ROOT), file_name]
    # Compile the document
    DEVNULL = open(os.devnull, 'w')
    subprocess.call(command, stdout=DEVNULL, stderr=subprocess.STDOUT)

    return user_specific_name[:-3]+'pdf'

##  Changed to download
#    subject = "MAT237 - PDF document"
#    message = "Your compiled document is attached"
#
#    email = EmailMessage(subject, message, 'mat237summer2016@gmail.com', [user.email])
#    try:
#        email.attach_file(file_name[0:-3]+"pdf")
#        email.send()
#        response_data = {'response': 'Email sent successfully'}
#
#        delete_command = ["rm", "-f", "{filename}*".format(filename=file_name[0:-3])]
#        subprocess.call(delete_command, stdout=DEVNULL, stderr=subprocess.STDOUT)
#    except Exception as e:
#        response_data = {'response': 'No document created. Likely an error in your code.'}
#        print(e)
#
#    return response_data


## ----------------- PDFLATEX ----------------------- ## 

# ----------------- HISTORY ----------------------- # 

@staff_required()
def poll_history(request, questionpk, poll_num=None):
    """ A view handler for a staff member to view poll question histories.
        Input: questionpk - an integer corresponding to the primary key for the pollquestion
               poll_num   - a number corresponding to the value of the poll. -1 indicates all polls
    """

    question = get_object_or_404(PollQuestion, pk=questionpk)

#    try:
    data = request.GET
    return_data = {}
    if poll_num == "-1":
        choices = question.pollchoice_set.all()
    elif poll_num is not None:
        choices = question.pollchoice_set.filter(cur_poll=int(poll_num))
        num_votes = sum(choices.values_list('num_votes', flat=True))
        return_data['votes']    = num_votes
    else:
        choices = question.pollchoice_set.filter(cur_poll=question.num_poll)
        num_votes = sum(choices.values_list('num_votes', flat=True))
        return_data['votes']    = num_votes

    return_data['question'] = question
    return_data['choices']  = choices
    return_data['poll_num'] = int(poll_num)
    
    return render(request, 'Problems/poll_history.html', return_data)

#    except Exception as e:
#        raise Http404('An error occured in processing your request. Exception: ' + str(e))

@staff_required()
def who_voted(request, questionpk, poll_num):
    """ Post the usernames of the students who voted in the given question, and how they voted
        Input: questionpk (integer) - Number corresponding to the question primary key
                 poll_num (integer) - The current poll number
        Output: HttpResponse
        Context: List of tuples (username, vote_id)
    """

    question = get_object_or_404(PollQuestion, pk=questionpk)
    choices  = question.pollchoice_set.filter(cur_poll=int(poll_num))

    student_votes = StudentVote.objects.filter(question=question, cur_poll=poll_num).values_list('student__username', 'vote__pk')

#    iterators = []
#    # For each choice correspond to the question, generate the list of students who voted on that question.
#    # The for loop creates an iterator, then we chain together the iterators at the end.
#    for choice in choices:
#        student_voters = choice.student_set.all().values_list('username', flat=True)
#        iterators.append(itertools.product(student_voters, [choice.pk]))
#
#    student_list = itertools.chain.from_iterable(iterators)

    return render(request, 'Problems/who_voted.html', 
            {
                'list': student_votes,
            })

# ----------------- (fold) History ----------------------- #

@staff_required()
def create_file_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            post = form.save()
            return redirect(post_announcements)
    else:
        form = CategoryForm()

    return render(request, 'Problems/edit_announcement.html', {'form' : form})


@staff_required()
def upload_file(request):
    if request.method == "POST":
        form = LinkedDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            file_item = form.save(commit=False)
            file_item.user = request.user
            file_item.save()
            success_string = "File successfully uploaded."
            redirect_string   = '<a href="{url}">Return to Administration Page</a>'.format(url=reverse('administrative'))
            return render(request, 'Problems/success.html', {'success_string': success_string, 'redirect_string': redirect_string})
    else:
        form = LinkedDocumentForm()

    return render(request, 'Problems/edit_announcement.html', {'form' : form})

# ----------------- (end) History ----------------------- #

# --------------------- (fold) Entropy --------------------- #

@staff_required()
def dump_polls(request):
    """ Private view for seeing all polls, ordered according to their Shannon entropy"""
    
    all_poll_questions = PollQuestion.objects.all()
    
    # Create a list, each of whose element is a dictionary containing the problem statement and the choices.
    # We will later sort this last based on the Shannon entropy of each pairing
    ret_polls = []
    for question in all_poll_questions:
        for cur_poll_num in range(1,question.num_poll+1):
            this_poll_choices = question.pollchoice_set.filter(cur_poll=int(cur_poll_num))

            if len(this_poll_choices) == 0:
                continue

            total_votes = sum(this_poll_choices.values_list('num_votes', flat=True))
            temp_dict = {'question_statement': question.text,
                         'choices': this_poll_choices,
                         'votes': total_votes,
                         'poll_question': question,
                        }
            entropy = compute_entropy(temp_dict)
            temp_dict.update({'entropy': entropy})
            ret_polls.append(temp_dict)

    ret_polls = sorted(ret_polls, key= lambda choice: compute_entropy(choice) , reverse=True)
    
    paginator = Paginator(ret_polls, 50)
    page = request.GET.get('page')
    try:
        polls = paginator.page(page)
    except PageNotAnInteger:
        polls = paginator.page(1)
    except EmptyPage:
        polls = paginator.page(paginator.num_pages)

    return render(request, 'Problems/dump_polls.html',
            {'polls': polls}
            )


def compute_entropy(question_dictionary):
    """ Takes a dictionary element from 'dump_polls' and computes its Shannon Entropy """
    choices     = question_dictionary['choices']
    total_votes = sum(choices.values_list('num_votes', flat=True))
        
    entropy = 0;
    for choice in choices:
        if choice.num_votes != 0:
            norm_prob = float(choice.num_votes)/float(total_votes)
            entropy  -= norm_prob*math.log(norm_prob,2)

    return entropy

# --------------------- (end) Entropy -------------------- #

# ---------- Quizzes (fold) ---------- #

# ---------- Quiz Add/Edit/Admin (fold) ---------- #

@staff_required()
def new_quiz(request):
    """ Form for creating a new quiz. Requires
        TODO: Check against 'can_edit_quiz" privileges.
    """
    if not request.user.is_staff:
        raise HttpResponse('You are not authorized to create quizzes')

    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.update_out_of()
            # Create an exemption type for the quiz and update it's out_of field
            evaluation, created = Evaluation.objects.get_or_create(name=quiz.name)
            evaluation.quiz_update_out_of(quiz)
            
            # For database convenience, populate the category as well. Updates will be made
            # in the function 'display_question', which will also take care of any student whose
            # record was not made to begin with
            #ret_flag = populate_category_helper(exemption)
            return redirect('quizzes')
    else:
        form = QuizForm()

    return render(
        request, 
        'Problems/edit_announcement.html', 
        { 'form' : form,
          'header': "Add Quiz to Course",
        }
    )

@staff_required()
def edit_quiz(request, quiz_pk):
    """ Fetches a quiz instance to populate an editable form. 
        <<Input>>
        quiz_pk - (Integers) The primary key for the quiz and course
        respectively.
    """

    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            quiz = form.save()
            quiz.update_out_of()
            # Since we might have changed the quiz's score, we also need to fix the
            # exemption score
            evaluation, created = Evaluation.objects.get_or_create(name=quiz.name)
            evaluation.quiz_update_out_of(quiz)
            return redirect('quiz_admin', quiz_pk=quiz.pk)
    else:
        form = QuizForm(instance=quiz)
        return render(
            request, 
            'Problems/edit_announcement.html', 
            { 'form' : form,
              'header': 'Edit Quiz',
            }
        )

@login_required
def list_quizzes(request, message=''):
    """ Show the list of all quizzes, including the live ones. Includes an adminstrative
    portion for staff. Can be redirected to when max-attempts on a live quiz is reached
    <<Input>> 
    message (String) default = '' A message to return to the student
    TODO: Need to add new row level privileges
    """
    all_quizzes = Quiz.objects.all()
    if request.user.is_staff:
        all_quizzes_table = AllQuizTable(all_quizzes)
        RequestConfig(request, paginate={'per_page', 10}).configure(all_quizzes_table)
    else:
        all_quizzes_table = ''

    live_quiz   = all_quizzes.filter(live__lte=timezone.now(), expires__gt=timezone.now())

    # Get this specific user's previous quiz results
    student_sqrs = StudentQuizResult.objects.select_related(
        'quiz').filter(student=request.user).order_by('quiz')
    # Now we need to filter these according to whether the solutions_are_visible
    # property is true on each quiz
    student_sqrs = [sqr for sqr in student_sqrs if sqr.quiz.solutions_are_visible]
    student_quizzes = SQRTable(student_sqrs)
    RequestConfig(request, paginate={'per_page': 10}).configure(student_quizzes)

    return render(request, 'Problems/list_quizzes.html', 
            {'live_quiz': live_quiz, 
             'all_quizzes': all_quizzes,
             'student_quizzes': student_quizzes,
             'all_quizzes_table': all_quizzes_table,
             'message': message,
            });

@staff_required()
def quiz_admin(request, quiz_pk):
    """ Generates the quiz administration page.
        <<Input>>
        quiz_pk (Integers) The primary keys for the quiz
        respectively.
        TODO: Change access dependencies to new row privileges.
    """
    quiz      = get_object_or_404(Quiz,pk=quiz_pk)

    questions = MarkedQuestionTable(quiz.markedquestion_set.all())
    RequestConfig(request, paginate={'per_page': 25}).configure(questions)
#    questions = quiz.markedquestion_set.all()

    return render(request, 'Problems/quiz_admin.html',
        { 'quiz': quiz,
          'questions': questions,
        }
    )

@staff_required()
def edit_quiz_question(request, quiz_pk, mq_pk=None):
    """ View designed to add/edit a question. If mq_pk is None then we make the
        question, otherwise we design the form to be edited.
    """

    quiz = get_object_or_404(Quiz, pk=quiz_pk)

    if mq_pk is None: # Adding a new question, so create the form.
        if request.method == "POST":
            form = MarkedQuestionForm(request.POST)
            if form.is_valid():
                mquestion = form.save(commit=False)
                mquestion.update(quiz)
                # Also update the exemption score, if necessary
                evaluation, created = Evaluation.objects.get_or_create(
                        name=mquestion.quiz.name)
                evaluation.quiz_update_out_of(mquestion.quiz)
                return redirect('edit_choices', quiz_pk=quiz_pk, mq_pk=mquestion.pk)
        else:
            form = MarkedQuestionForm()
    else: # Editing a question, so populate with current question
        mquestion = get_object_or_404(MarkedQuestion, pk=mq_pk)
        if request.method == "POST":
            form = MarkedQuestionForm(request.POST, instance=mquestion)
            if form.is_valid():
                mquestion = form.save(commit=False)
                mquestion.update(quiz)
                mquestion.quiz.update_out_of()
                # Also update the exemption score, if necessary
                evaluation, created = Evaluation.objects.get_or_create(
                        name=mquestion.quiz.name)
                evaluation.quiz_update_out_of(mquestion.quiz)

                # Check to see if there are any possible issues with the format of the question
                return redirect('edit_choices', quiz_pk=quiz.pk, mq_pk=mquestion.pk)
        else:
            form = MarkedQuestionForm(instance=mquestion)

    sidenote = """
    <h4> Notes </h4>
    <ul class="mathrender">
        <li>LaTeX brackets must be double bracketed. For example, <code> e^{{ {v[0]} x}}</code>
        <li>You may use mathematical symbols, such as +,-,*,/ in your answer.
        <li>Exponentiation is indicated by using a**b; for example, \(2^3\) may be entered as 2**3
        <li>You may use the functions \(\sin, \cos,\\tan, \ln\) in your answer.
        <li>You may use the constants pi and e for  \(\pi\)  and \(e\).
        <li>You may use the python math package in your functions. For example, <code>{"f": lambda x: math.sqrt(x) }</code>
        <li> Use 'rand(-5,10)' to create a random integer in the range [-5,10] (inclusive). Use 'uni(-1,1,2)' to create a real number in [-1,1] with 2 floating points of accuracy
    </ul>"""

    return render(request, 'Problems/edit_announcement.html', 
        { 'form': form,
          'sidenote': sidenote,
          'header': "Create Quiz Question",
        }
    )

def deserialize(s_str):
    """ Helper function. Takes a string which embodies a list of choices for the variable
        inputs and returns the python object.
        <<Input>>
        s_str (String) - A string serializing the list of choices
        <<Output>>
        list object which contains the possible choices.
    """

    if s_str is None:
        return []

    prelist = s_str.replace(' ','') # Kill all extra whitespace
    split_list = prelist.split(';') # Semi-colons separate list elements
    choices = []
    for index, sublist in enumerate(split_list):
        choices.append(sublist.split(',')) # Commas separate elements which each list

    return choices

def choice_is_valid(string, num_vars):
    """ Determine whether input string is a valid choice; that is, either an integer or
        a correctly formatted randomization string.
        Input: string (String) - to be validated
               num_vars - (Integer) - necessary number of variables
        Output: Boolean - indicating whether the string is valid
                err_msg - error message
    """
    parts = string.replace(' ', '').split(';')
    return_value = True
    error_message = "Choice is valid"

    if len(parts) != num_vars:
        return False, "Incorrect number of variables. Given {}, expected {}".format(len(parts), num_vars)

    # We run the function parse_abstract_choice. If it works then the input is valid, otherwise it's not
    try:
        parse_abstract_choice(string)
    except:
        error_message = "Invalid input. Please insert the current number of variables, with appropriate range."
        return_value = False

#    for part in parts:
#        match = re.match(r'[zZ](-?\d+),(-?\d+)',part)
#        if isnumber(part):
#            return_value*= True
#        elif match:
#            if int(match.group(1))<int(match.group(2)):
#                return_value*= True
#            else:
#                return_value*= False
#                error_message = "Integer range out of order."
#        else:
#            error_message = "Invalid input. Please insert the current number of variables, with appropriate range."
#            return_value*= False
    return return_value, error_message


def isnumber(string):
    try:
        float(string)
        return True
    except:
        return False

def edit_choices(request, quiz_pk, mq_pk):
    """ After adding/editing a MarkedQuestion object, we need to specify the
        choices, which indicates what types of values can be substituted into
        the variables {v[i]}. 
        View which handles the ability to add/edit choices.
        <<Input>>
        quiz_pk (Integers) Not really needed, but for consistent urls
        mq_pk (integer) the marked question primary key
    """

    mquestion = get_object_or_404(
        MarkedQuestion.objects.select_related('quiz'), 
        pk=mq_pk
    )
    error_message = ''

    if request.method == "POST":
        form_data = request.POST
        try:
            updated_choices = ''
            # On post, we go through all the current choices and update them
            for field, data in form_data.items():
                if 'choice' in field:
                    cur_choice = form_data[field]
                    
                    # If cur_choice is empty, it's likely a delete-submission, so we skip it
                    if cur_choice == '':
                        continue

                    # Verify that our choices are correctly formatted
                    is_valid, msg = choice_is_valid(cur_choice, mquestion.num_vars)
                    if is_valid:
                        # We do not want extraneous semi-colons, so we have to check to see if we are
                        # first element of updated choices
                        if len(updated_choices) == 0:
                            updated_choices = cur_choice
                        else:
                            updated_choices = updated_choices + ":" + cur_choice
                    else:
                        raise Exception(msg)

            mquestion.choices = updated_choices
            mquestion.save()
        except Exception as e:
            error_message = e
            print(e)

    if mquestion.choices is None or mquestion.choices == "":
        choices = ""
    else:
        choices = mquestion.choices.split(":")

    return render(request, 'Problems/edit_choices.html',
            {
                "mquestion": mquestion,
                "choices": choices,
                "error_message": error_message,
            })

@staff_required()
def search_students(request):
    """ AJAX view for searching for a student's records.
    """
    try:
        if not request.user.is_staff:
            return HttpResponseForbidden('Insufficient privileges')

        if 'query' in request.GET:
            query = request.GET['query']

            fields = ["username__contains", "first_name__contains", "last_name__contains",]
            queries = [Q(**{f:query}) for f in fields]
            qs = Q()
            for query in queries:
                qs = qs | query

            # Filter by course as well
            users = User.objects.filter(qs).distinct()
            ret_list = users[0:10]
#            for user in users:
#                try:
#                    if course in user.membership.courses.all():
#                        ret_list.append(user)
#                except Exception as e:
#                    continue #membership might not exist

            return render(request, 'Problems/search_students.html',
                { 'users': ret_list,
                }
            )

    except Exception as e:
        print(str(e))
        raise Http404('Invalid request type')

@staff_required()
def student_results(request, user_pk):
    if not request.user.is_staff:
        return HttpResponseForbidden('Insufficient Privileges')
    student = get_object_or_404(User, pk=user_pk)
    # Get this specific user's previous quiz results
    student_quizzes = SQRTable(
        StudentQuizResult.objects.select_related(
            'quiz').filter(student=student).order_by('quiz')
    )
    RequestConfig(request, paginate={'per_page': 10}).configure(student_quizzes)

    return render(request, 'Problems/student_results.html', 
            { 'student_quizzes': student_quizzes,
              'student': student,
            });

# ---------- Quiz Add/Edit/Admin (end) ---------- #

# ---------- Quiz Handler (fold) ---------- #

@login_required
def start_quiz(request, quiz_pk):
    """ View to handle when a student begins a quiz. 
        <<Input>>
        quiz_pk (integer) - corresponding to the primary key of the quiz
        <<Output>>
        HttpResponse object. Renders quizzes/start_quiz.html or redirects 
                                     to display_question

        Depends on: generate_next_question
    """

    this_quiz = get_object_or_404(
            Quiz, 
            pk=quiz_pk, 
            live__lte=timezone.now(), 
            expires__gt=timezone.now())
    
    # Get the StudentQuizResults corresponding to this student. If there are
    # none, this is the first try. If there are some, we need to find the most
    # current one (ie the one with the largest `attempt' attribute. Then we need
    # to check if that StudentQuizResult is still in progress, or if a new
    # attempt needs to be created. In the latter, we also need to check that the
    # student has not surpassed the number of attempts permitted
    student = request.user
    quiz_results = StudentQuizResult.objects.filter(
            student=student, quiz=this_quiz).select_related(
                'quiz')
    high_score = -1
   
    # The user may be allowed several attempts. We need to determine what attempt the 
    # user is on, and whether they are in the middle of a quiz
    is_new = False;
    if len(quiz_results) == 0: # First attempt
        # Should be made into an SQR manager method
        #cur_quiz_res = StudentQuizResult( student=student, quiz=this_quiz, attempt=1, score=0, result='{}',cur_quest = 1)
        #cur_quiz_res.save()
        cur_quiz_res = StudentQuizResult.create_new_record(student,this_quiz)
        generate_next_question(cur_quiz_res)
        is_new = True
    else: 
        # Determine the most recent attempt by finding the max 'attempt'
        quiz_aggregate = quiz_results.aggregate(Max('attempt'), Max('score'))
        most_recent_attempt = quiz_aggregate['attempt__max']
        high_score = quiz_aggregate['score__max']
        cur_quiz_res = quiz_results.get(attempt=most_recent_attempt)
        # Now we need to check if this attempt was finished. Recall that if cur_quest = 0
        # then all questions are finished. If all questions are finished, we must also check
        # if the student is allowed any more attempts
        if (cur_quiz_res.cur_quest == 0): # Current attempt is over.
            if (most_recent_attempt < this_quiz.tries or this_quiz.tries == 0): # Allowed more tries
                # Should be made into an SQR manager method
                #cur_quiz_res = StudentQuizResult(student=student, quiz=this_quiz, attempt=most_recent_attempt+1,score=0,result='{}',cur_quest=1)
                #cur_quiz_res.save()
                cur_quiz_res = StudentQuizResult.create_new_record(
                    student, this_quiz, most_recent_attempt+1)
                generate_next_question(cur_quiz_res) #Should make this a model method
                is_new = True
            else: # No more tries allowed
                message = "Maximum number of attempts reached for {quiz_name}.".format(quiz_name=this_quiz.name)
                return list_quizzes(request, message=message) # Returns a view

    # Need to genererate the first question
    return render(request, 'Problems/start_quiz.html', 
            {'record': cur_quiz_res, 
             'quiz': this_quiz,
             'high_score': high_score,
             })

def eval_sub_expression(string, question):
    """ Used to evaluate @-sign delimited subexpressions in sentences which do
        not totally render. Variables should be passed into the string first,
        before passing to this function.  For example, if a string is if the
        form: "What is half of \(@2*{v[0]}@\)" then we should have already
        substituted {v[0]} into the string, so that eval_sub_expression
        receives, for example, "What is half of \(@2*3@\)?"
    
        <<INPUT>>
        string (String) containing (possibly zero) @-delimited expressions.
        question (MarkedQuestion) object. Contains the user-defined functions.
        <<OUTPUT>>
        That string, but with the @ signs removed and the internal expression
        evaluated.
    """

    # If no subexpression can be found, simply return

    if not "@" in string:
        return post_process(string)

    temp_string = string
    pattern = re.compile(r'@(.+?)@')
    functions = eval(question.functions)
    functions.update(settings.PREDEFINED_FUNCTIONS)
    try:
        while "@" in temp_string:
            match = pattern.search(temp_string)
            # Evaluate the expression and substitute it back into the string
            replacement = simple_eval(
                    match.group(1),
                    names=settings.UNIVERSAL_CONSTANTS, 
                    functions=functions
                    )
            try: # Round if a number
                replacement = round(replacement,4)
            except TypeError as e: #Otherwise it's a string do nothing
                pass
            except Exception as e:
                raise e

            temp_string = temp_string[:match.start()] + str(replacement) + temp_string[match.end():]

    except Exception as e: # Should expand the error handling here. What can go wrong?
        raise e

    temp_string = post_process(temp_string)

    return temp_string

def post_process(input_string):
    """ Hack fix to certain math problems, such as 1x, a^1, or +- or --.
        <<INPUT>>
        input_string (String) The string to process
    """
    temp_string = input_string
    
    # List of regex's to find issues, and their replacement string
    regex_patterns = [
        (re.compile(r'(?<!\d)1\s*(\\?[a-zA-Z])'), r'\g<1>'), # Should match 1x and replace with x
        (re.compile(r'(\w*)\^1'), 'r\g<1>'), # Matches a^1 and replaces with a
        (re.compile(r'(\w*)\^{{\s*1\s*}}'), 'r\g<1>'), # Matches a^1 and replaces with a
        (re.compile(r'\+\s*\-'), '-'), #Matches +- and replaces with -
        (re.compile(r'\-\-'), '+'), #matches -- and replaces with +
    ]

    for pat, repl in regex_patterns:
        temp_string = pat.sub(repl, temp_string)

    return temp_string

def sub_into_question_string(question, choices):
    """ Given a MarkedQuestion object and a particular choice set for the
        variables {v[0]}=5, {v[1]}=-10, etc, substitute tese into the problem
        and return the string.
        <<INPUT>
        question (MarkedQuestion) object 
        choices (string) for the choices to insert into the question text. For
            example, if question.problem_str has variables {v[0]} and {v[1]},
            then choices should be something of the form "5;-10", in which case
            we make the substitution {v[0]} = 5, {v[1]} = -10.
        <<OUTPUT>> 
        A string rendered correctly.

        Depends on: eval_sub_expression 
    """
    problem = question.problem_str # Grab the question string
    # Remove any troublesome white space, and split the choices (delimited by a
    # semi-colon). Then substitute them into the sring.
    problem = problem.format(v=choices.replace(' ', '').split(';'))

    # Pass the string through the sub-expression generator
    problem = eval_sub_expression(problem, question)
    return problem

def strip_string(string):
    """ Remove all line breaks and spaces from a string:
    """
    fix_list = [
        ('\r', ''),
        ('\n', ''),
        (' ',  ''),
    ]
 
    temp_string = string
 
    for fix in fix_list:
        temp_string = temp_string.replace(fix[0], fix[1])
 
    return temp_string
 

def mark_question(sqr, string_answer, accuracy=10e-5):
    """ Helper question to check if the answers are the same. Updates SQR
        internally and returns a boolean flag indicating whether this is the
        last question.
        <<INPUT>>
        sqr (StudentQuizResult) - the quiz record
        string_answer (string) - the correct answer
        accuracy (float) - The desired accuracy. Default is 10e-5;
            that is, four decimal places.
        <<OUTPUT>>
        is_last (Boolean) - indicates if the last question has been marked
    """
    # Result is a python dict, qnum is the attempt of the quiz
    result, qnum = sqr.get_result() 

    # Already the last question, so don't check anything and return true
    if qnum == '0':
        return True

    correct = result[qnum]['answer']

    # For multiple choice questions, we do not want to evaluate, just compare strings
    if result[qnum]['type'] == "MC":
        if strip_string(str(correct)) == strip_string(string_answer):
            result[qnum]['score']='1'
            sqr.update_score()
        else:
            result[qnum]['score']='0'

        result[qnum]['guess']        = string_answer 
        result[qnum]['guess_string'] = string_answer 

    else:
        correct = float(correct) # Recast to float for numeric comparison
        
        try:
            guess = round(
                simple_eval(
                    string_answer, 
                    names=settings.UNIVERSAL_CONSTANTS, 
                    functions=settings.PREDEFINED_FUNCTIONS
                ),
            4) #numeric input, rounds to 4 decimal places
            result[qnum]['guess'] = guess
            result[qnum]['guess_string'] = string_answer
        except Exception as e:
            raise ValueError('Input could not be mathematically parsed.')

        if (abs(correct-guess)<accuracy): # Correct answer
            result[qnum]['score']='1'
            sqr.update_score()
        else:
            result[qnum]['score']='0'

    sqr.update_result(result)
    is_last = sqr.add_question_number()
    return is_last

def generate_next_question(sqr):
    """ Given a StudentQuizResult, creates a new question. Most often this
        function will be called after a question has been marked and a new one
        needs to be created. However, it is also used to instantiate the first
        question of a quiz.  
        <<INPUT>>
        sqr (StudentQuizResult) contains all the appropriate information for
            generating a new question 
        <<OUTPUT>>
        q_string (String)  The generated question, formated in a math renderable
            way 
        mc_choices (String) The multiple choice options

        Depends on: get_mc_choices, sub_into_question_string
    """
    result, qnum = sqr.get_result()
    # The following is defined so it can be returned, but is only ever used if
    # question type is MC
    mc_choices = ''

    # the cur_quest value of sqr should always correspond to the new question,
    # as it is updated before calling this function. We randomly choose an
    # element from quiz.category = sqr.cur_quest, and from that question we then
    # choose a random choice, possibly randomizing yet a third time of the
    # choices are also random
    try:
        question = sqr.quiz.get_random_question(sqr.q_order[sqr.cur_quest-1])
    except IndexError as e:
        print(e)

    # From this question, we now choose a random input choice
    a_choice = question.get_random_choice()

    # This choice could either be a tuple of numbers, a randomizer, or a mix. We
    # need to parse these into actual numbers
    choices = parse_abstract_choice(a_choice)
    answer = get_answer(question, choices)

    #Feed this into the result dictionary, and pass it back to the model
    result[qnum] = {
            'pk': str(question.pk),
            'inputs': choices,
            'score': '0',
            'answer': answer,
            'guess': None,
            'type': question.q_type
            }
    
    # If the question we grabbed is multiple choice, then we must also generate
    # the multiple choice options.
    if question.q_type == "MC":
        mc_choices = get_mc_choices(question, choices, answer)
        result[qnum].update({'mc_choices': mc_choices})
    
    sqr.update_result(result)

    return sub_into_question_string(question,choices), mc_choices

def get_mc_choices(question, choices, answer):
    """ Given a question and a choice for the variable inputs, get the multiple
        choice options.
        <<INPUT>>
        question (MarkedQuestion)
        choices  (String) corresponding to the concrete choices for the v[0],...,v[n]
        answer   (String) to concatenate to the choices list
        <<OUTPUT>> 
        A list of strings with numeric values. For example ['13', '24', '52.3',
            'None of the above']

        ToDo: Allow for @-sign based delimeter expressions. May want to do this
        based on the exception raised on simple_eval
    """
    split_choices = choices.split(';')
    mc_choices = []

    for part in question.mc_choices.split(';'):
        """ Internal flow: See if variables are present. If so, substitute the
            variables. If not, it's hard coded.  If we do not find variables but
            cannot evaluate, the answer is a sentence/word. So just append it.
        """
        if re.findall(r'{v\[\d+\]}', part): # matches no variables
            part = part.format(v=split_choices)
            part = eval_sub_expression(part, question)

        try:
            # Remove troublesome whitespace as well
            eval_string = part.replace(' ','')
            value = round(
                simple_eval(
                    eval_string, 
                    functions=settings.PREDEFINED_FUNCTIONS,
                    names=settings.UNIVERSAL_CONSTANTS
                ),
            4)
                
            mc_choices.append(str(value))
        except: #If not an exectuable string, then it must be a hardcoded answer
            mc_choices.append(part)

    mc_choices.append(str(answer))

    # Now shuffle them.
    random.shuffle(mc_choices)

    return mc_choices

def parse_abstract_choice(abstract_choice):
    """ Parses an abstract choice into a concrete choice. Expects a single
        choice input. Currently can only handle integer ranges.
        <<INPUT>>
        abstract_choice (String) - Used to indicate an abstract choice,
            separated by ';'
        <<OUTPUT>>
        (String) A concrete choice 
    """
    choice = ''
    for part in abstract_choice.replace(' ', '').split(';'):
        if isnumber(part): # If already a number
            choice += part + ";"
        else: # it must be a command, one of 'rand' or 'uni'
            pre_choice = simple_eval(
                part, 
                names=settings.UNIVERSAL_CONSTANTS,
                functions=settings.PREDEFINED_FUNCTIONS
            )
            choice += str(pre_choice)+";"

#        elif part[0] in 'zZ':
#            lower, upper = [int(x) for x in part[1:].split(',')]
#            if upper==lower: # Ensures we can't accidentally enter an infinite loop on Z0,0
#                concrete = str(upper) + ";"
#            else:
#                concrete = random.randint(lower,upper)
#                if part[0].istitle(): # Range specifies non-zero number using capital letter
#                    while concrete == 0:
#                        concrete = random.randint(lower,upper)
#            choice += str(concrete) + ";"

    # At the end, we need to cut off the trailing semi-colon
    return choice[0:-1]

def get_answer(question, choices):
    """ Evaluates the mathematical expression to compute the answer.
        <<INPUT>>
        question (MarkedQuestion) The object containing the question
        choices (String) String containing *concrete* choices
        <<OUTPUT>>
        (Integer)  The answer, to be saved

        Depends: simpleeval.simple_eval
    """
    answer = question.answer
    if choices is None:
        return answer
    if re.findall(r'{v\[\d+\]}', answer): # matches no variables
        answer = answer.format(v=choices.split(';'))
        answer = eval_sub_expression(answer, question)

    try:
        # Substitute the variables into the string and evaluate the functions dictionary
#        eval_string = answer.format(v=choices.split(';'))
        # Remove whitespace before evaluating
        eval_string = answer.replace(' ', '')
        functions = eval(question.functions)
        functions.update(settings.PREDEFINED_FUNCTIONS)

        return round(
            simple_eval(
                eval_string, 
                functions=functions, 
                names=settings.UNIVERSAL_CONSTANTS
            ),
        4)
    except (SyntaxError, NameNotDefined,) as e:
        # Enter this exception if the answer is not one that can be evaluated.
        # In that case, the answer is just the answer
#        if question.q_type == "MC":
#            return answer
#        else:
#            raise e
        return answer

    except Exception as e: 
        raise e

@login_required
def display_question(request, sqr_pk, submit=None):
    """ When a student accesses a quiz, there is a redirect to this view which
        shows the current question quiz-question. This view also handles the
        submission of an answer, checking the correct answer and generating
        either the next question or the results page. 
        <<INPUT>>
        sqr_pk (integer) indicating the StudentQuizResult primary key
        submit (Boolean default:None) Checks if the student is seeing the
            question (None/False) or has submitted an answer that we need to
            grade (True)
        <<OUTPUT>>
        HttpResponse - renders the quiz question

        <<DEPENDS>> 
          sub_into_question_string, mark_question,
          generate_next_question, update_marks
    """
    sqr = StudentQuizResult.objects.select_related('quiz').get(pk=sqr_pk)
    string_answer = ''
    error_message = ''
    mc_choices = None
    # Start by doing some validation to make sure only the correct student has
    # access to this page
    if sqr.student != request.user:
        return HttpResponseForbidden(
            'You are not authorized to see this question')

    # submit=None means the student is just viewing the question and hasn't
    # submitted a solution. In this case, simply render the question.
    if submit is None:
        result, qnum = sqr.get_result()
        # If qnum is 0, then the quiz is finished. In this case, render the
        # results page.
        if qnum == '0':
            result_table = get_result_table(sqr.result)
            return render(request, 'Problems/completed_quiz.html', 
                { 'sqr': sqr,
                  'result_table': result_table,
                }
            )
         
        # Otherwise, pick out the current question and its multiple choice
        # answers (if applicable).
        # result[qnum] has fields (MarkedQuestion) pk, inputs, score, type,
        # (mc_choices)
        question = MarkedQuestion.objects.get(pk=int(result[qnum]['pk']))
        choices  = result[qnum]['inputs']
        # Input the choices into the question string
        q_string = sub_into_question_string(question, choices)
        
        if result[qnum]['type'] == "MC":
            mc_choices = result[qnum]['mc_choices']
    # Information was submitted, so verify that the input is correctly
    # formmated, mark the question, and either return the results page (if done)
    # or generate the next question.
    else: 
        # The page was either refreshed or the table with the results was sorted
        if request.method == "GET": 
            result_table = get_result_table(sqr.result)
            RequestConfig(request, paginate={'per_page', 10}).configure(result_table)
            return render(request, 'Problems/completed_quiz.html', 
                { 'sqr': sqr,
                  'result_table': result_table,
                }
            )

        # Grab the question string in case we need to return the question on
        # error Note: I need to provide the above line with a default. If
        # sometimes throws an error for some reason. Also need to track down
        # this bug
        q_string = request.POST['problem'] 
        try:
            string_answer = request.POST['answer'] #string input
            # Mark the question. If it's the last question, is_last = True and
            # we generate the results page
            is_last = mark_question(sqr, string_answer)

            if not is_last: 
                # There are more questions, so generate the next one
                q_string, mc_choices = generate_next_question(sqr)
                string_answer = ''
            else: 
                # The quiz is over, so generate the result table. Also, update
                # the student mark
                result_table = get_result_table(sqr.result)
                # We are not tracking marks, so this is commented out
                update_marks(sqr) # Call a helper method for updating the student's marks 
                RequestConfig(request, paginate={'per_page', 10}).configure(result_table)
                return render(request, 'Problems/completed_quiz.html', 
                        {   'sqr': sqr,
                            'result_table': result_table,
                        })
                        
#            # For MC, this is ajax, so check
#            if request.is_ajax():
#                if not is_last:
#                    return_data = {'next_url': reverse('display_question', args=(sqrpk,))}
#                else:
#                    return_data = 
#                return HttpResponse(json.dumps(return_data))

        except ValueError as e:
            error_message =  ("The expression '{}' did not parse to a valid"
                " mathematical expression. Please try"
                " again").format(string_answer)
            # Technically if we get here, we do not have the mc_choices to
            # return if it was a multiple choice question; however, this should
            # never happen as it should be impossible to pass a bad input with
            # mc

    return render(request, 'Problems/display_question.html', 
        { 'sqr': sqr,
          'question': q_string, 
          'error_message': error_message,
          'string_answer': string_answer,
          'mc_choices': mc_choices,
         }
    )

def update_marks(quiz_result):
    """ Helper function for updating quiz marks once a quiz has been completed.
        Input: quiz_record (StudentQuizResult)
    """
    try:
        evaluation, cr = Evaluation.objects.get_or_create(
                name=quiz_result.quiz.name)
        # Should rarely need to be triggered, but if a quiz was imported without
        # creating an evaluation, the first student who writes it will create the
        # evaluation. Hence we also need to update the out_of
        if cr: 
            evaluation.quiz_update_out_of(quiz_result.quiz)
        cur_grade, created = StudentMark.objects.get_or_create(
                        user = quiz_result.student,
                        category = evaluation
                    )
        cur_grade.set_score(quiz_result.score, 'HIGH')
    except Exception as e:
        print(e)

def get_result_table(result):
    """ Turns the string StudentQuizResults.results and generated a table.
        <<INPUT>>
        result (string) serialized JSON object to be converted to a table
        <<OUTPUT>
        QuizResulTable populated with the data.
    """
    
    ret_data = []
    res_dict = json.loads(result)
    for field, data in res_dict.items():
        part = {'q_num': int(field), 
                'correct': str(data['answer']), 
                'guess': str(data['guess']),
                'score': data['score']}
        ret_data.append(part)
    
    return QuizResultTable(ret_data)

@staff_required()
def test_quiz_question(request, quiz_pk, mq_pk):
    """ Generates many examples of the given question for testing purpose.
        Input: mpk (Integer) MarkedQuestion primary key

        Depends on: sub_into_question_string, render_html_for_question
    """
    mquestion = get_object_or_404(
            MarkedQuestion.objects.select_related('quiz'), 
            pk=mq_pk)

    if not request.user.is_staff:
        return HttpResponseForbidden('You are not authorized to test this.')

    if request.method == "POST": # Testing the question
        num_tests = request.POST['num_tests']
        html = ''

        try:
            for k in range(0,int(num_tests)):
                choice = parse_abstract_choice(mquestion.get_random_choice())
                answer = get_answer(mquestion, choice)

                if mquestion.q_type == "MC":
                    mc_choices = get_mc_choices(mquestion, choice, answer)
                else:
                    mc_choices = ''

                problem = sub_into_question_string(mquestion, choice)
                
                html += render_html_for_question(problem, answer, choice, mc_choices)
                # Should add better error handling here.
        except KeyError as e:
            html = ("Key Error: Likely an instance of single braces '{{,'}} when"
            " double braces should have been used. See the code<br>"
            " '{{ {} }}'").format(str(e))
        except AttributeError as e:
            html = ("Attribute Error: Likely you failed to close a @..@ group"
                    " or have an unbalanced @ group. See the code <br>"
            " '{{ {} }}'").format(str(e))
        except SyntaxError as e:
            html = ("Syntax Error: Evaluation failed. Did you forget to "
                    "use an arithmetic operator? <br>"
                    " '{{ {} }}'").format(str(e))
        except Exception as e:
            html = e

        return HttpResponse(html)

    else:
        return render(request, 'Problems/test_quiz_question.html',
                {'mquestion':mquestion,
                })

def render_html_for_question(problem, answer, choice, mc_choices):
    """ Takes in question elements and returns the corresponding html.
        Input: problem (String) The problem 
               answer  (float) the correct answer
               choice  (String) a ';' separated tuple of variable choices
               mc_choices (string) a list of multiple choice options
    """

    template = """
               <div class = "mathrender quiz-divs question-detail">
                   {problem}
               </div>
               
               <ul>
                   <li><b>Answer:</b> {answer}
                   <li><b>Choice:</b> {choice}
               </ul>
               """.format(problem=problem, answer=answer, choice=choice)
    if mc_choices:
        template += "<ul>\n"
        for choice in mc_choices:
            template+= "<li>{choice}</li>\n".format(choice=choice)

        template +="</ul>\n"

    return template

@login_required
def quiz_details(request, sqr_pk):
    """ A view which allows students to see the details of a
        completed/in-progress quiz.  
        <<INPUT>>
        sqr_pk (int) The primary key of the quiz result

    Depends on: sub_into_question_string
    """

    quiz_results = get_object_or_404(
        StudentQuizResult.objects.select_related('quiz'), 
        pk=sqr_pk)

    # Ensure you're looking at your own results or you're an admin
    if not ( (request.user == quiz_results.student) 
                or
             (request.user.is_staff)
           ):
        return HttpResponseForbidden()

    # Next ensure that you are allowed to see the results
    if not (quiz_results.quiz.solutions_are_visible or request.user.is_staff):
        raise Http404('Solutions are unavailable at this time')

    result_dict = quiz_results.get_result()[0]
    template = """
    <li> 
        <div class = "mathrender question-detail">
            {problem}
        </div>
        {correct}
        <ul>
            <li><b>Correct Answer</b>: <span class="mathrender">{answer}</span>
            <li><b>Your Answer</b>: <span class="mathrender">&quot;{guess_string}&quot; evaluated to {guess}</span>
        </ul>
    """

    #Generate the return html
    return_html = ""
    for qnum in range(1,len(result_dict)+1):
        temp_dict = result_dict[str(qnum)]

        #Check to see if the question has been answered. If not, skip it
        if 'guess_string' not in temp_dict:
            continue

        mquestion = MarkedQuestion.objects.get(pk = temp_dict['pk'])

        problem = sub_into_question_string(mquestion, temp_dict['inputs'])

        c_mark = ''
        if int(temp_dict['score']):
            c_temp = "<p style='color:green'><span class='text'>Correct</span>{}</p>"
        else:
            c_temp = "<p style='color:red'><span class='text'>Incorrect</span>{}</p>"

        if request.user.is_staff:
            c_mark=(" <small style='color:blue; cursor:pointer' class='change_mark' data-id={}>"
                      "(Change)"
                      "</small>").format(qnum)
        correct = c_temp.format(c_mark)
        
        return_html += template.format(problem=problem, 
                                       correct=correct,
                                       answer=temp_dict['answer'],
                                       guess_string=temp_dict['guess_string'],
                                       guess=temp_dict['guess'])

    # return_html only has body. Need to wrap on ordered-list
    return_html = "<ol> {} </ol>".format(return_html)
    return render(request, 'Problems/quiz_details.html',
            {'return_html': return_html,
             'sqr': quiz_results,
            })
            
@staff_required()
def change_mark(request):
    """
        Used to easily change a student mark.
    """
    try:
        if request.method == "POST":
            sqr_pk = request.POST['sqr_pk']
            qnum = request.POST['qnum']
            sqr = get_object_or_404(
                StudentQuizResult.objects.select_related('quiz'), 
                pk=int(sqr_pk)
            )
            res, _ = sqr.get_result()
            res[qnum]['score'] =str( int(not int(res[qnum]['score'])))
            sqr.update_result(res)
            # Update the score. update_score by default adds one to the score,
            # but takes option argument 'minus' to subtract. We modify based off
            # the new score.
            sqr.update_score(not int(res[qnum]['score']))

            # Finally, we update the marks
            update_marks(sqr)

            return HttpResponse(json.dumps({'result': 'success'}))

    except Exception as e:
        return HttpResponse(json.dumps({'result': str(e)}))

# ---------- Quiz Handler (end) ---------- #

# ---------- Quizzes (end) ---------- #
#
# -------------------- Student Note (fold) ----------------------- #

@login_required
def upload_student_note(request):
    """ Handles student note uploads. Both new note and editing.
    """

    sidenote = """<ul>
    <li>File must be of pdf, png, or jpeg format
    <li>File cannot be larger than 1000KB.
    </ul>"""

    if request.method == "POST":
        form = StudentDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            file_item = form.save(commit=False)
            file_item.update_user(request.user)
            success_string = "File successfully uploaded."
            redirect_location = reverse('get_note', args=(file_item.doc_file.name,))
            redirect_string   = '<a href="{url}">Click to verify upload.</a>'.format(url=redirect_location)
            return render(request, 'Problems/success.html', 
                    {'success_string': success_string, 
                     'redirect_string': redirect_string
                    })
    else:
        form = StudentDocumentForm()
        
    return render(request, 'Problems/edit_announcement.html', 
            {'form' : form,
             'sidenote': sidenote,
            })

@login_required
def see_notes(request):
    user = request.user

    note_table = NotesTable(StudentDocument.objects.filter(user=user))

    return render(request, 'Problems/list_table.html', 
                  {'table': note_table,
                   'title': 'Sick Notes',
                  })

@login_required
def get_note(request, filename):
    user = request.user
    try:
        note = StudentDocument.objects.get(doc_file=filename)
        path = note.doc_file.path
    except AttributeError as e:
        return HttpResponse('No such note')
        
    # Need to make sure students can only see their own files, or you are a staff member
    if (user == note.user) or (user.is_staff):
        return sendfile(request, path)
    else:
        return HttpResponseForbidden()
    
    #Need to hunt down the file name and pass the path to the webserver with an X-SENDFILE header

def get_student_notes(search_string='', max_results=10):
    """ Returns a list of students.
        Inputs: serach_string='' (String)
                max_results = 10 (Integer)
        Ouput: list of notes matching the string criterion
    """

    return_list= []
    return_list = StudentDocument.objects.filter(user__username__contains=search_string)

    if max_results >0:
        if len(return_list) > max_results:
            return_list=return_list[:max_results]

    return return_list

@staff_required()
def search_notes(request):
    """ View for an instructor to view and approve notes.
        Also handles the AJAX calls for searching
    """

    if request.is_ajax():
        list_of_students = []
        contains = ''
        if 'suggestion' in request.GET:
            search_string = request.GET['suggestion']
            list_of_notes = get_student_notes(search_string)

            return render(request, 'Problems/list_of_students.html',
                    {'list_of_notes': list_of_notes}
                    )

        if request.method == "POST":
            try:
                accepted = request.POST['accepted'] == 'true'
                notepk = request.POST['pk']

                note = StudentDocument.objects.get(pk=notepk)
                note.change_accepted(accepted)

                return HttpResponse("Note modified")
            except Exception as e:
                return HttpResponse(e)

    else:
        ajax_url = reverse('search_notes')
        return render(request, 'Problems/search_notes.html',
                {'ajax_url': ajax_url
                })

@staff_required()
def create_exemption(request, exemption_pk=None):
    """ Administrative view for creating/editing a request.
    """
    if not exemption_pk: # Create a new exemption
        if request.method == "POST":
            form = ExemptionForm(request.POST)
            if form.is_valid():
                exemption = form.save()

                ret_flag = populate_category_helper(exemption)
                success_string = "New exemption created and populated."
                redirect_string = '<a href="{url}">Return to Admin Page</a>'.format(url=reverse('administrative'))
                return render(request, 
                      'Problems/success.html', 
                      { 'success_string': success_string, 
                        'redirect_string': redirect_string,
                      })
        else:
            form = ExemptionForm()
    else: # Editing a question, so populate with current question
        exemption = get_object_or_404(Evaluation, pk=mpk)
        if request.method == "POST":
            form = ExemptionForm(request.POST, instance=exemption)
            if form.is_valid():
                exemption = form.save()

                # Check to see if there are any possible issues with the format of the question
                return redirect('administrative')
        else:
            form = ExemptionForm(instance=exemption)

    return render(request, 'Problems/edit_announcement.html', {"form": form})

# --------------- (end) Notes --------------- #

# Though the previous method is used in Marks #
# --------------- (fold) Marks --------------- #

def populate_category_helper(category):
    """ Helper method for populating a category.
        Input: category (Evaluation) category to populate
        Out  : return_flag - (0) Exception
                             (1) Success
                             (2) Already populated, nothing performed
    """

    if StudentMark.objects.filter(category=category).count():
        return 2

    try:
        students = User.objects.filter(is_staff=False)
        bulk_list = []
        for student in students:
            bulk_list.append(StudentMark(user=student, category=category))

        StudentMark.objects.bulk_create(bulk_list)
        return 1
    except Exception as e:
        return 0

@staff_required()
def populate_category(request):
    """ Once a category is created, use this view to populate it; that is,
        we create a StudentMark element for each student in the course.
        Input: exemption_pk (Integer) - the primary key of the category
    """

    # students are precisely those users who are not staff members
    
    if request.method == "POST":
        
        try:
            exemption_pk = int(request.POST['exemption'])
            category = get_object_or_404(Evaluation, pk=exemption_pk)
        except:
            raise Http404('Non integer primary key')

        ret_flag = populate_category_helper(category)

        if ret_flag == 2:
            success_string = "{category} already populated. No further action required".format(category=category.name)
        elif ret_flag == 1:
            success_string = "{category} successfully populated.".format(category=category.name)
        else:
            success_string = "There was an error in populating the category"

        redirect_string = '<a href="{url}">Return to Previous Page</a>'.format(url=reverse('administrative'))

        return render(request, 
                      'Problems/success.html', 
                      { 'success_string': success_string, 
                        'redirect_string': redirect_string,
                      })
    else:
        form = PopulateCategoryForm()
        return render(request, 'Problems/edit_announcement.html', {'form': form} )

@login_required
def see_marks(request):
    """ A view for students to see their current marks.
    """

    user  = request.user
    marks = StudentMark.objects.filter(user=user)

    marks_table = MarksTable(marks)

    sidenote = """<h4>Comments</h4>
    If you have submitted a note to be exempted from an assessment,
    it will appear in this table. Notably,
    <ul>
        <li> <b>Submitted</b>: The note has been submitted but not yet accepted.
        <li> <b>Exempt</b>: The note has been accepted, and you are exempt from
        the assessment.
    </ul>
    </div>
    """

    return render(request, 'Problems/list_table.html', 
                  {'table': marks_table,
                   'title': 'Current Marks',
                   'sidenote': sidenote,
                  })

def append_to_log(the_dict, log_location):
    """ A helper function which appends to a python dictionary to a data-log.
        Inputs: the_dict (Dictionary) - A python dictionary to be appended
                log_location (string) - The path to the log-file
        Return: Void
    """

    # We will use JSON serialization. Open the log as an 'append', and dump the dictionary
    with open(log_location, 'a') as f:
        json.dump(the_dict, f)
        f.write(os.linesep)

@staff_required()
def marks_search(request):
    if request.is_ajax():
        query = request.GET['query']
        cat   = request.GET['category']

        category = get_object_or_404(Evaluation, pk=cat)

        # Search for StudentMark with category=cat and users satisfying the query
        fields = ["user__username__contains", "user__first_name__contains", "user__last_name__contains", "user__info__student_number__contains"]
        queries = [Q(**{f:query}) for f in fields]

        qs = Q()
        for query in queries:
            qs = qs | query

        marks = StudentMark.objects.filter(qs, category=category).distinct()
        table = MarkSubmitTable(marks)
        RequestConfig(request).configure(table)

    return render(request, 'Problems/render_table.html', {'table': table})

def create_marks_log_entry(smark, staff, old_score=''):
    """ Creates a python dictionary for logging data.
        Input: smark (StudentMark) object
               staff (User) who made the adjustment
               old_score (Optional, Integer) The old score
        Return: (Dictionary) consisting of
        {'staff': ___, 'category': ___, 'student': {'username': ___, 'pk': ___}, 'datetime': ___ }
    """

    return {'staff': staff.username,
            'category': smark.category.name,
            'student': {'username': smark.user.username,
                        'pk': smark.user.pk},
            'old_score': old_score,
            'new_score': smark.score,
            'datetime': str(timezone.now())
            }

def get_student_marks_for_table(student):
    """ A helper function which outputs the dictionary of student marks.
        Input: student (User) the student whose marks we are getting
        Return: (Dictionary) suitable for entry into djangot-tables2

        ToDo: Could see_marks benefit from this?
        Warning: If iterating over students, should prefetch marks
    """
    try:
        stud_num = student.info.student_number
    except Exception as e:
        stud_num = "No info"
    return_dict = {'last_name': student.last_name,
                   'first_name': student.first_name,
                   'username': student.username,
                   'number': stud_num}
    for smark in student.marks.iterator():
        notes = smark.has_note()
        if notes:
            if [note for note in notes if note.accepted]:
                score="Exempt"
            else:
                score="Submitted"
        else:
            score = smark.score

        return_dict[smark.category.name.replace(' ','')]=score
    return return_dict

def get_marks_data():
    """ Helper function for created the dictionary of student marks. Only looks
        at active students (non-staff members), and uses their student info. If
        student_info does not exist, that element is created and initialized
        with empty strings.
        Returns (Dict) Dictionary of student data, with fields
        {last_name, first_name, user_name, number}
        and a field for each Evaluation assessment
    """
    table_data = [];
    students = User.objects.prefetch_related(
        'marks', 'info', 'notes').filter(
        is_staff=False, is_active=True)
    for student in students:
        try:
            table_data.append(get_student_marks_for_table(student))
        except StudentInfo.DoesNotExist:
            # Make en empty StudentInfo object so that the student still appears in the grade sheet list
            student_info = StudentInfo(user=student,
                                student_number = '',
                                tutorial = '',
                                lecture = '')
            student_info.save()
            table_data.append(get_student_marks_for_table(student))

    return table_data

@staff_required()
def download_all_marks(request):
    """ For staff members to download the marks table as a csv file.
    """

    # This effectively starts the same was as the see_all_marks view, but
    # instead of rendering as a table, we write to a csv and set up a download
    # link
    table_data = get_marks_data()

    file_name = "All_grades_by_{user}_{date}.csv".format(
                    user = request.user,
                    date = timezone.now().timestamp())
    file_path = os.path.join(settings.NOTE_ROOT, file_name)

    # The csv DictWriter needs to know the field names.
    ident_names = [ 'last_name', 'first_name', 'username', 'number'] 
    cat_names   = Evaluation.objects.all().values_list('name', flat=True)
    # cat_names will have spaces in them, while table_data stripped spaces
    cat_names = [cat.replace(' ','') for cat in cat_names]
    field_names = ident_names + cat_names
    
    with open(file_path, 'a+') as csv_file:
        writer = csv.DictWriter(csv_file, field_names)
        writer.writeheader()
        for row in table_data:
            # Write each row to a csv file
            writer.writerow(row)
        
    return sendfile(request, file_path)

@staff_required()
def see_all_marks(request):
    """ A view for returning all student marks.
    """

    # [[[Added a method to handle this. Delete when confirmed works.]]]
    #
    # From scratch, we summon all student data. Ensure to prefetch the reverse relationships,
    # otherwise this will hit the database a lot
    #table_data = [];
    #students = User.objects.prefetch_related('marks', 'info', 'notes').filter(is_staff=False, is_active=True)
    #for student in students:
    #    try:
    #        table_data.append(get_student_marks_for_table(student))
    #    except StudentInfo.DoesNotExist:
    #        # Make en empty StudentInfo object so that the student still appears in the grade sheet list
    #        student_info = StudentInfo(user=student,
    #                            student_number = '',
    #                            tutorial = '',
    #                            lecture = '')
    #        student_info.save()
    #        table_data.append(get_student_marks_for_table(student))

    # Generate the table. This is dynamic to the number of categories which currently exists
    table_data = get_marks_data()
    table = define_all_marks_table()(table_data)
    RequestConfig(request, paginate=False).configure(table)

    sidenote = format_html("<h4>Options</h4><a class='btn btn-default' href='{}'>Download Marks</a>", 
                           reverse('download_all_marks'))
    return render(request, 'Problems/list_table.html',
            {'table': table,
             'title': 'All Marks',
             'sidenote': sidenote,
            })

@staff_required()
def submit_marks(request, category='', tutorial='all'):
    """ A view for populating a table and submitting marks.
        Input: category (String) indicating the primary key of the category.

        AJAX: Requires input (score, category, user), which are strings but can
              be cast as (float, int, int). Returns json element
              'success': (Boolean) indicating whether the mark was successfuly recorded
              'response': (String) with a message
    """

    #Standard handling
    if request.method == "GET":

        # We always need this to populate the scroller
        list_of_categories = Evaluation.objects.all()
        # Get the list of tutorials
        tuts = Tutorial.objects.all()

        if category:
            try:
                this_category = list_of_categories.filter(pk=int(category))
            except Exception as e:
                raise Http404('No such category: {}'.format(str(e)))
        else:
            try:
                this_category = list_of_categories.latest('id')
                category = str(this_category.pk)
            except Exception as e:
                raise Http404('No mark objects')

        if tutorial != 'all':
            try:
                tut = tuts.get(name=tutorial)
                tut_name = tut.name
                marks = StudentMark.objects.filter(
                    category=this_category,
                    user__info__tutorial = tut,
                    )
            except Exception as e:
                raise Http404('No such tutorial: {}'.format(str(e)))
        else:
            tut_name = 'all'
            marks = StudentMark.objects.filter(category=this_category)

        table = MarkSubmitTable(marks)
        RequestConfig(request).configure(table)

        #Get the address of the ajax method (which is just this view as well)
        ajax_url = reverse('submit_marks')

        return render(request, 'Problems/submit_marks.html',
                {'table':table,
                 'category': category,
                 'list_of_categories': list_of_categories,
                 'ajax_url': ajax_url,
                 'tut_name': tut_name,
                 'tuts': tuts,
                })

    elif request.method == "POST": # Score input
        data_dict = request.POST
        try:
            score = float(data_dict['score'])
            cat   = int(data_dict['category'])
            user  = int(data_dict['user'])

            category = get_object_or_404(Evaluation, pk=cat)
            user     = get_object_or_404(User, pk=user)
            smark    = StudentMark.objects.get(user=user, category=category)

            old_score = smark.set_score(score)

            response_string= "Mark for {user} successfully recorded".format(user=user.username)
            ret_data = {'success': True, 'response':response_string}
            
            log_entry = create_marks_log_entry(smark,request.user, old_score)
            append_to_log(log_entry, settings.MARKS_LOG)

        except Exception as e:
            ret_data = {'success': False, 'response': str(e)}

        return HttpResponse(json.dumps(ret_data))


# ------------------ (end) Marks  ------------------ #

# ------------------ Typos (fold) ------------------ #

def submit_typo(request, url_redirect=''):
    """ View for handling typo submissions. In particular, checks if user is logged in. If the
        user is not logged in, then we must return a human verification checkbox.
    """
   
    # If user is anonymous
    if request.user.username:
        user = request.user
    else:
        user = None 

    # If post, then form was submitted
    if request.method == "POST":
        form = TypoForm(request.POST)
        # Check to see that user is logged in, or verified human
        if (user is not None or 'check-cap' in request.POST):
            if form.is_valid():
                post = form.save(commit=False)
                post.set_user(user)

                if not url_redirect:
                    url_redirect = reverse('administrative')

                success_string = "Typo successfully submitted."
                redirect_string = '<a href="{url}">Return to Previous Page</a>'.format(url=url_redirect)

                return render(request, 
                              'Problems/success.html', 
                              { 'success_string': success_string, 
                                'redirect_string': redirect_string,
                              })

        else: # Return the form
            return render(request, 
                          'Problems/typo_form.html', 
                          { 'form' : form,
                            'user' : user,
                          })
    else:
        form = TypoForm()

    return render(request, 
                  'Problems/typo_form.html', 
                  { 'form' : form,
                    'user' : user,
                  })

def see_typos(request, document=''):
    """ Displays the typos, ordered by page and document. If user is staff
        then also gives unverified typos.
    """

    if document == "all":
        if request.user.is_staff:
            typos = Typo.objects.all()
        else:
            typos = Typo.objects.filter(verified=True)
    else:
        if request.user.is_staff:
            typos = Typo.objects.filter(document=document)
        else:
            typos = Typo.objects.filter(verified=True, document=document)

    typos=typos.order_by('page')

    typos_url  = reverse('see_typos')
    verify_url = reverse('verify_typo')

    if request.is_ajax():
        return render(request, 'Problems/base_typo.html',
                {'typos': typos,
                })

    return render(request, 'Problems/see_typos.html', 
            {'typos': typos,
             'typos_url': typos_url,
             'verify_url': verify_url,
             'document': document,
            })

@staff_required()
def edit_typo(request, typopk, url_redirect=''):
    """ Edits a typo. Expects url_redirect to be the document type for see_typos
    """
    typo = get_object_or_404(Typo, pk=typopk)
    if request.method == "POST":
        form = TypoForm(request.POST, instance=typo)
        if form.is_valid():
            typo = form.save()
            return redirect(reverse('see_typos', kwargs={'document': url_redirect}))
    else:
        form = TypoForm(instance=typo)

    return render(request, 'Problems/edit_announcement.html', 
            {'form' : form,
            })

@staff_required()
def verify_typo(request):
    """ Verifies a typo. Should be done by ajax.
        Expects: 'typopk' in POST, which is the primary key of the Typo object
    """

    if request.method =="POST":
        response_dict = {}
        try:
            typopk = int(request.POST['typopk'])
            typo = get_object_or_404(Typo, pk=typopk)
            typo.verify()
            response_dict['response'] = "Typo verified"
            response_dict['flag'] = 0
        except Exception as e:
            response_dict['response'] = "Error: {}".format(e)
            response_dict['flag'] = 1

        return HttpResponse(json.dumps(response_dict))

# ------------------ Typos (end) ------------------ #

@staff_required()
def latex_playground(request):
    """ A view for people to play around with latex.
    """

    file_path = settings.MEDIA_ROOT + "/latex_help.txt"
    with open(file_path, 'r') as f:
        latex_help = f.read()

    return render(request, 'Problems/latex_playground.html',
            {'latex_help': latex_help,
            })

# ------------------ Tutorials (fold) ------------------ #

@login_required
def change_tutorial(request):
    """ Allows students to change tutorials at will.
        Todo: Add administrator certification of change
    """
    if request.method == "POST": # Form submitted
        try:
            # Read the tutorial number from the form and get the 
            # tutorial object
            tut_pk   = int(request.POST['tutorial'])
            tutorial = get_object_or_404(Tutorial, pk=tut_pk)

            # Get the user's student information so that we can update
            user = request.user
            info = StudentInfo.objects.get(user__username=user.username)

            info.change_tutorial(tutorial)
        except Exception as e:
            print(e)
            raise Http404(str(e))

        success_string = ("Your tutorial was successfully changed to "
                          "TUT{}.".format(tutorial.name)
                         )
        redirect_string = '<a href="{url}">Return to Administration Page</a>'.format(url=reverse('administrative'))

        return render(request, 
                      'Problems/success.html', 
                      { 'success_string': success_string, 
                        'redirect_string': redirect_string,
                      })
    else:
        form = ChangeTutorialForm()
        return render(request, 'Problems/edit_announcement.html', {'form': form} )

# ------------------ Tutorials (end)  ------------------ #

# --------------------- (fold) Upload Data --------------------- #

# These views emulate the management commands for resetting the active students
# (unecessary if remote authentication is used), and uploading marks. Uses Comma
# Separated Value (CSV) files for upload. Identifying model should be username
# or student_number

def extract_csv_data(the_file, as_dict=False):
    """ Takes a csv file and extracts the data.
        Input: 
            the_file (File) - the csv file
            as_dict (Bool)  - Default is False, and will return a 2d array.
                              Otherwise, will return a dictionary.
    """
    ret_data = []
    with open(the_file.path, 'rt') as csv_file:
        for row in csv.reader(csv_file):
            if as_dict:
                this_row = {'student_number': row[0], 'grade': row[1]}
            else:
                this_row = row

            ret_data.append(this_row)

    return ret_data

def backup_current_grades(category, user):
    """ Creates a CSVBackup model element with a backup for the grades. Called
        'upload_marks_file'.
        Input:
            category - (Evaluation) specifying which assessment is to be
                       backed up.
        Output:
            (CSVBackup) Model element containing the backup information
    """
    list_of_students = User.objects.select_related('info').filter(is_active=True, is_staff=False)

    file_name = "{cat}_backup_by_{user}_{date}.csv".format(
                    cat  = category.name,
                    user = user,
                    date = timezone.now().timestamp())
    file_path = os.path.join(settings.NOTE_ROOT, file_name)
    
    with open(file_path, 'a+') as csv_file:
        the_writer = csv.writer(csv_file, delimiter=',')
        for student in list_of_students:
            # Write each student's current grade to a csv file. Use that file to
            # create a CSVBackup element.
            stud_mark, created = StudentMark.objects.get_or_create(
                                    user     = student,
                                    category = category)
            if created:
                stud_mark.set_score(0)

            the_writer.writerow([student.info.student_number, stud_mark.score])

        # With the CSV file written, create a CSVBackup element
        backup_file = CSVBackup(user = user,
                                file_name = file_name,
                                category = category)
        backup_file.doc_file.save(file_name, File(csv_file))

    return backup_file

def error_report_and_backup(log_location, backup_file):
    """ Internal method for creating the large html string necessary to report
        the results of the grade-change view.
        Input: (String) log_location
               (CSVBackup) backup_file
        Ouput: (String) With html for the success.html template
    """
    # Need to provide two pieces of information. The results in the error log,
    # and the location of the backup file

    backup = """
    <p> The backup file is located in a file named {name} on the server, under a
    model name of {model}
    """.format(name=backup_file.doc_file.name, 
               model=backup_file.file_name)

    # Open the log and feed it to the error report
    try:
        with open(log_location, 'r') as the_error_log:
            error = the_error_log.read()

        if not error:
            error = "No errors in uploading"
    except:
        error = "No error log"

    template = """<p>Operation was successful.</p>
    <br>
    <h4>Backup Information</h4>
    {backup}
    <h4>Error Information</h4>
    {error}
    <br><br>""".format(backup=backup, error=error)

    return template
    
@staff_required()
def upload_marks_file(request, csvfile_pk=None):
    """ A simple form for uploading a csv file. First column must be username,
        second column is the grade
        csvfile_pk - In form POST, has the primary key for the CSVBackup file
        containing the marks
    """
    if request.method == "POST":
        # Two options: Either first submitting the data, or confirming after the
        # preview. The preview is distinguished by csvfile_pk.
        if csvfile_pk:
            # Recall that saved CSV file and update the student marks
            csv_file = CSVBackup.objects.get(pk=csvfile_pk)
            category = csv_file.category
            table_data = extract_csv_data(csv_file.doc_file)

            # Initialize the logger to track the old grades and the new grades
            log_name = "{cat}_backup_{timestamp}".format(
                            cat=category, 
                            timestamp=timezone.now().timestamp())
            log_location = "/".join([settings.LOG_ROOT, log_name])
            # Deprecated: Now using append_to_log for custom logging
            #logging.basicConfig(filename=log_location, level=logging.DEBUG)

            # Backup the current grades, then make the changes
            backup_file = backup_current_grades(category, request.user)

            for row in table_data:
                try:
                    # More pythonic to do [student_number, score] in table data,
                    # but doesn't check against invalid information
                    [uname, score] = row
                    try:
                        user = User.objects.get(username=uname)
                    except Exception as e:
                        message='Error for entry {}: {} <br>'.format(row, e)
                        append_to_log(message, log_location)
                        continue

                    if not score:
                        score = 0

                    stud_mark, created = StudentMark.objects.get_or_create(
                                            user=user,
                                            category=category)
                    # Once I change the StudentMark scheme to allow floats in
                    # score, this line will need to be changed to remove 'round'
                    stud_mark.set_score(float(score))
                except Exception as e:
                    string = ("ERROR: {first} {last} with username: {username}."
                              "\n Exception: {e}").format(
                              first=first_name, last=last_name, username=username, e=e)
                    append_to_log(string, log_location)

            success_string  = error_report_and_backup(log_location, backup_file) 

            redirect_string = '<a href="{url}">Visit Marks Page</a>'.format(
                                        url=reverse('see_all_marks'))
            return render(request, 
                          'Problems/success.html', 
                          { 'success_string': success_string, 
                            'redirect_string': redirect_string})

        else:
            form = CSVBackupForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.save(commit=False)
                csv_file.set_user_and_name(request.user)

                # Create the preview and push the link to this csv file through
                table_data = extract_csv_data(csv_file.doc_file, as_dict=True)
                table = CSVPreviewTable(table_data)

                return render(request, 'Problems/preview_csv.html', 
                        {'table':      table,
                         'assessment': csv_file.category.name,
                         'csv_pk':     csv_file.pk,
                        })
    else:
        # No POST, which means accessing the page for the first time.
        form = CSVBackupForm(include_cat=True)
        
    sidenote = ("First column must be the student number, the second column"
                " is the grade.")

    return render(request, 'Problems/edit_announcement.html', 
            {'form' : form,
             'sidenote': sidenote,
            })



# --------------------- (end) Upload Data --------------------- #
