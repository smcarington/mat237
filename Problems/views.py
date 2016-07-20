from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.views import password_change
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail, EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import Max

from django_tables2 import RequestConfig

import json
import subprocess
import os
import re
import itertools
import math
from operator import attrgetter

from django.contrib.auth.models import User
from .models import Announcement, ProblemSet, Question, QuestionStatus, Poll, PollQuestion, PollChoice, LinkedDocument, StudentVote
from .forms import AnnouncementForm, QuestionForm, ProblemSetForm, NewStudentUserForm, PollForm, LinkedDocumentForm, TextFieldForm
import random
import math
from simpleeval import simple_eval, NameNotDefined

from django.contrib.auth.models import User
from .models import Announcement, ProblemSet, Question, QuestionStatus, Poll, PollQuestion, PollChoice, LinkedDocument, Quiz, MarkedQuestion, StudentQuizResult
from .forms import AnnouncementForm, QuestionForm, ProblemSetForm, NewStudentUserForm, PollForm, LinkedDocumentForm, TextFieldForm, QuizForm, MarkedQuestionForm
from .tables import MarkedQuestionTable, AllQuizTable, QuizResultTable, SQRTable

# Create your views here.

def staff_required(login_url='/accounts/login/'):
    return user_passes_test(lambda u:u.is_staff, login_url=login_url)

# @login_required
def post_announcements(request):
    posts = Announcement.objects.filter(expires__gte=timezone.now()).order_by('-stickied', '-published_date')
    return render(request, 'Problems/post_announcements.html', {'announcements': posts})

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
    return render(request, 'Problems/calendar.html')

@login_required
def notes(request):
    # Post links in the sidebar
    docs = LinkedDocument.objects.select_related('category').all().order_by('category')
    cat_names = docs.values_list('category__cat_name', flat=True).distinct()
    return render(request, 'Problems/notes.html', {'docs':docs, 'cats':cat_names})

@staff_required()
def administrative(request):
    if request.user.is_staff:
        return render(request, 'Problems/administrative.html')
    else:
        return HttpResponseForbidden()

@login_required
def list_problem_set(request, pk):
    ps = get_object_or_404(ProblemSet, pk=pk)

    # There is no standary sort_by on the charfield that returns difficulty, so we use the 'extra' method
    #CASE_SQL = '(case when difficulty="E" then 1 when difficulty="M" then 2 when difficulty="H" then 3 when difficulty="I" then 4 end)'
    #problems = ps.problems.extra(select={'difficulty': CASE_SQL}, order_by=['difficulty'])
    problems = ps.problems.order_by('difficulty', 'pk')
    return render(request, 'Problems/list_problem_set.html', {'problems': problems, 'problem_set': ps})

@csrf_protect
@login_required
def question_details(request, pk):
    problem = get_object_or_404(Question, pk=pk)
    problemStatus, created = QuestionStatus.objects.get_or_create(user=request.user, question=problem)

    if request.method == "POST":
        solution = request.POST['solution']
        problemStatus.solution = solution
        problemStatus.save()

    return render(request, 'Problems/question_details.html', {'problem': problem, 'status': problemStatus})

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
        raise HttpResponseForbidden()

    return HttpResponse(json.dumps(response_data))

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
        
        subject = "You have just been added to MAT237!"
        message = """ You have just been added to the MAT237 course website, located at

http://www.utmat237.com

Your username is {username} and your password is {password}. 
Please login and change your password
            """.format(username=un, password=rpass)

        send_mail(subject, message, 'mat237summer2016@gmail.com', [em])
        user.save()

        # Now send a confirmation to the staff member who added this user
        conf_subject = "User {student} has just been added to MAT237".format(student=un)
        conf_message = """The Student with the email address {email} and username {student} has been successfully added to the MAT237 group user list. No further action is required on your part.""".format(student=un, email=em)

        try:
            send_mail(conf_subject, conf_message, 'mat237summer2016@gmail.com', [request.user.email], fail_silently=False)
        except:
            print('Error sending confirmation email to staff member')

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
        svote, created = StudentVote.objects.get_or_create(student=request.user, cur_poll = choice.cur_poll, question=choice.question)

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
        ps_title = "Problem Set {num}".format(num=str(problem_set))
        latex_source = create_latex_source(qlist, ps_title)
        # Sanitize the string of html tags
        latex_source = latexify_string(latex_source)
        # Send the file to be compiled and emailed using another helper function
        response_data = compile_and_email(latex_source, user)

        return HttpResponse(json.dumps(response_data))

    else:
        raise Http404('Request not posted')

def latexify_string(string):
    """ A helper function which accepts a latex html string, possibly including tags,
        and returns a string where those tags have been appropriate replaced with
        LaTeX commands. For example, <ol>...</ol> will become \\begin{enumerate}...
        \\end{enumerate}
    """

    ret_string = string
    ret_string = re.sub(r'<ol>', r'\\begin{enumerate}', ret_string)
    ret_string = re.sub(r'</ol>', r'\\end{enumerate}', ret_string)
    ret_string = re.sub(r'<ul>', r'\\begin{itemize}', ret_string)
    ret_string = re.sub(r'</ul>', r'\\end{itemize}', ret_string)
    ret_string = re.sub(r'<li>', r'\\item ', ret_string)
    ret_string = re.sub(r'(<br>)+', r'\\', ret_string)
    ret_string = re.sub(r'<b>(.*)</b>', r'\\textbf{\1}', ret_string)
    ret_string = re.sub(r'<i>(.*)</i>', r'\\emph{\1}', ret_string)
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

def compile_and_email(latex_source, user):
    """ A helper function for the function 'pdflatex'. Accepts a string with the full latex
        source code. Creates a file with this string, compiles it, and emails it to the user.
        Input: latex_source - A (string) containing the latex source code.
               user         - (User) element corresponding to session user.
        Out  : A (string) indicating the success/failure of the method.
    """

    # Write the string to a file so that we can curl it to the external server
    latex_directory = "/".join([settings.MEDIA_ROOT, "latex"])
    file_name = "/".join([latex_directory, "latex_{userpk}.tex".format(userpk=user.pk)])
    with open(file_name, 'w') as f:
        f.write(latex_source)
    
    command = ["pdflatex", "-halt-on-error", "-output-directory={dir}".format(dir=latex_directory), file_name]
    # Compile the document
    DEVNULL = open(os.devnull, 'w')
    subprocess.call(command, stdout=DEVNULL, stderr=subprocess.STDOUT)
    print("done compiling")

    subject = "MAT237 - PDF document"
    message = "Your compiled document is attached"

    email = EmailMessage(subject, message, 'mat237summer2016@gmail.com', [user.email])
    try:
        email.attach_file(file_name[0:-3]+"pdf")
        email.send()
        response_data = {'response': 'Email sent successfully'}

        delete_command = ["rm", "-f", "{filename}*".format(filename=file_name[0:-3])]
        subprocess.call(delete_command, stdout=DEVNULL, stderr=subprocess.STDOUT)
    except Exception as e:
        response_data = {'response': 'No document created. Likely an error in your code.'}
        print(e)

    return response_data
## ----------------- PDFLATEX ----------------------- ## 

## ----------------- HISTORY ----------------------- ## 

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

## ----------------- HISTORY ----------------------- ## 

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

## ------------------ ENTROPY ---------------------- ##

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
## ----------------- MARKED QUESTIONS ----------------------- ## 

@staff_required()
def new_quiz(request):
    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.update_out_of()
            return redirect(administrative)
    else:
        form = QuizForm()

    return render(request, 'Problems/edit_announcement.html', {'form' : form})

@staff_required()
def edit_quiz(request, quizpk):
    """ Fetches a quiz instance to populate an editable form."""

    quiz = get_object_or_404(Quiz, pk=quizpk)
    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            quiz = form.save()
            quiz.update_out_of()
            return redirect('quiz_admin', quizpk=quiz.pk)
    else:
        form = QuizForm(instance=quiz)
        return render(request, 'Problems/edit_announcement.html', {'form' : form})

@login_required
def quizzes(request, message=''):
    """ Show the list of all quizzes, including the live ones. Includes an adminstrative
    portion for staff. Can be redirected to when max-attempts on a live quiz is reached
    Input: message (String) default = '' A message to return to the student
    """
    all_quizzes = Quiz.objects.all()
    if request.user.is_staff:
        all_quizzes_table = AllQuizTable(all_quizzes)
        RequestConfig(request, paginate={'per_page', 10}).configure(all_quizzes_table)
    else:
        all_quizzes_table = ''

    live_quiz   = all_quizzes.filter(live__lte=timezone.now(), expires__gt=timezone.now())

    # Get this specific user's previous quiz results
    student_quizzes = SQRTable(StudentQuizResult.objects.filter(student=request.user).order_by('quiz'))
    RequestConfig(request, paginate={'per_page': 10}).configure(student_quizzes)

    return render(request, 'Problems/list_quizzes.html', 
            {'live_quiz': live_quiz, 
             'all_quizzes': all_quizzes,
             'student_quizzes': student_quizzes,
             'all_quizzes_table': all_quizzes_table,
             'message': message,
            });

@staff_required()
def quiz_admin(request, quizpk):
    quiz      = get_object_or_404(Quiz,pk=quizpk)

    questions = MarkedQuestionTable(quiz.markedquestion_set.all())
    RequestConfig(request, paginate={'per_page': 25}).configure(questions)
#    questions = quiz.markedquestion_set.all()

    return render(request, 'Problems/quiz_admin.html',
            {
             'quiz': quiz,
             'questions': questions
            });

@staff_required()
def edit_quiz_question(request, quizpk, mpk=None):
    """
        View designed to add/edit a question. If mpk is None then we make the question, otherwise
        we design the form to be edited.
    """

    quiz = get_object_or_404(Quiz, pk=quizpk)

    if mpk is None: # Adding a new question, so create the form.
        if request.method == "POST":
            form = MarkedQuestionForm(request.POST)
            if form.is_valid():
                mquestion = form.save(commit=False)
                mquestion.update(quiz)
                return redirect('edit_choices', mpk=mquestion.pk)
        else:
            form = MarkedQuestionForm()
    else: # Editing a question, so populate with current question
        mquestion = get_object_or_404(MarkedQuestion, pk=mpk)
        if request.method == "POST":
            form = MarkedQuestionForm(request.POST, instance=mquestion)
            if form.is_valid():
                mquestion = form.save(commit=False)
                mquestion.update(quiz)
                mquestion.quiz.update_out_of()

                # Check to see if there are any possible issues with the format of the question
                return redirect('quiz_admin', quizpk=quiz.pk)
        else:
            form = MarkedQuestionForm(instance=mquestion)

    sidenote = """
    <h4> Notes </h4>
    <ul class="diff">
        <li>LaTeX brackets must be double bracketed. For example, <code> e^{{ {v[0]} x}}</code>
        <li>You may use mathematical symbols, such as +,-,*,/ in your answer.
        <li>Exponentiation is indicated by using a**b; for example, \(2^3\) may be entered as 2**3
        <li>You may use the functions \(\sin, \cos,\\tan, \ln\) in your answer.
        <li>You may use the constants pi and e for  \(\pi\)  and \(e\).
        <li>You may use the python math package in your functions. For example, <code>{"f": lambda x: math.sqrt(x) }</code>
        <li> Use 'rand(-5,10)' to create a random integer in the range [-5,10] (inclusive). Use 'uni(-1,1,2)' to create a real number in [-1,1] with 2 floating points of accuracy
    </ul>"""

    return render(request, 'Problems/edit_announcement.html', 
            {'form': form,
             'sidenote': sidenote})

def deserialize(s_str):
    """
        Helper function. Takes a string which embodies a list of choices for the variable
        inputs and returns the python object.
        
        Input: s_str (String) - A string serializing the list of choices
        Output: list object which contains the possible choices.
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


@staff_required()
def edit_choices(request, mpk):
    """
        View which handles the ability to add/edit choices.
        Input: mpk - (integer) the marked question primary key
    """

    mquestion = get_object_or_404(MarkedQuestion, pk=mpk)
    error_message = ''

    if request.method == "POST":
        form_data = request.POST
        try:
            updated_choices = ''
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

@login_required
def start_quiz(request, quizpk):
    """ View to handle when a student begins a quiz.
        Input: quizpk (integer) - corresponding to the primary key of the quiz
        Output: HttpResponse object. Renders Problems/start_quiz.html or redirects 
                                     to display_question
    """

    this_quiz = get_object_or_404(Quiz, pk=quizpk, live__lte=timezone.now(), expires__gt=timezone.now())
    
    student = request.user
    quiz_results = StudentQuizResult.objects.filter(student=student, quiz=this_quiz)
    high_score = -1
   
    # The user may be allowed several attempts. We need to determine what attempt the 
    # user is on, and whether they are in the middle of a quiz
    
    is_new = False;
    if len(quiz_results) == 0: # First attempt
        cur_quiz_res = StudentQuizResult(
                student=student, 
                quiz=this_quiz, 
                attempt=1, 
                score=0, 
                result='{}',
                cur_quest = 1
                )
        cur_quiz_res.save()
        generate_next_question(cur_quiz_res)
        is_new = True
    else:
        # Determine the most recent attempt
        quiz_aggregate = quiz_results.aggregate(Max('attempt'), Max('score'))
        most_recent_attempt = quiz_aggregate['attempt__max']
        high_score = quiz_aggregate['score__max']
        cur_quiz_res = quiz_results.get(attempt=most_recent_attempt)
        # Now we need to check if this attempt was finished. Recall that if cur_quest = 0
        # then all questions are finished. If all questions are finished, we must also check
        # if the student is allowed any more attempts
        if (cur_quiz_res.cur_quest == 0): # Current attempt is over.
            if (most_recent_attempt < this_quiz.tries or this_quiz.tries == 0): # Allowed more tries
                cur_quiz_res = StudentQuizResult(
                    student=student, 
                    quiz=this_quiz, 
                    attempt=most_recent_attempt+1,
                    score=0,
                    result='{}',
                    cur_quest=1)
                cur_quiz_res.save()
                generate_next_question(cur_quiz_res) #Should make this a model method
                is_new = True
            else: # No more tries allowed
                message = "Maximum number of attempts reached for {quiz_name}.".format(quiz_name=this_quiz.name)
                return quizzes(request, message)

    # Need to genererate the first question
    return render(request, 'Problems/start_quiz.html', 
            {'record': cur_quiz_res, 
             'quiz': this_quiz,
             'high_score': high_score,
             })

def get_return_string(question,choices):
    """ Renders a math-readable string for displaying to a student.
        Input:  question (MarkedQuestion) object 
                choices (string) for the choices to insert into the question text
        Output: A string rendered correctly.
    """
    problem = question.problem_str
    return problem.format(v=choices.replace(' ', '').split(';'))

    #numbers = [ float(x) for x in choices.replace(' ', '').split(';') ]
    #
    #return problem.format(v=numbers)

def mark_question(sqr, string_answer, accuracy=10e-5):
    """ Helper question to check if the answers are the same.
        Input: sqr (StudentQuizResult) - the quiz record
               string_answer (string) - the correct answer
               accuracy (float) - The desired accuracy. Default is 10e-5;
                                  that is, four decimal places.
        Output: is_last (Boolean) - indicates if the last question has been marked
    """
    result, qnum = sqr.get_result()

    # Already the last question, so don't check anything and return true
    if qnum=='0':
        return True

    correct = result[qnum]['answer']

    # For multiple choice questions, we do not want to evaluate, just compare strings
    if result[qnum]['type'] == "MC":
        if str(correct) == string_answer:
            result[qnum]['score']='1'
            sqr.update_score()
        else:
            result[qnum]['score']='0'

        result[qnum]['guess']        = string_answer 
        result[qnum]['guess_string'] = string_answer 

    else:
        correct = float(correct) # Recast to float for numeric comparison
        
        try:
            guess   = round(simple_eval(string_answer, 
                                names=settings.UNIVERSAL_CONSTANTS, 
                                functions=settings.PREDEFINED_FUNCTIONS),4) #numeric input
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
    """ Given a StudentQuizResult, creates a new question. Most often this function will be called
        after a question has been marked and a new one needs to be created. However, it is also used
        to instantiate the first question of a quiz.
        Input: sqr (StudentQuizResult) - contains all the appropriate information for generating a new
                                         question
        Output: q_string (String) - The generated question, formated in a math renderable way
               mc_choices (String) - The multiple choice options
    """
    result, qnum = sqr.get_result()
    # The following is defined so it can be returned, but is only ever used if question type is MC
    mc_choices = ''

    # the cur_quest value of sqr should always correspond to the new question, as it is updated before
    # calling this function. We randomly choose an element from quiz.category = sqr.cur_quest, and from
    # that question we then choose a random choice, possibly randomizing yet a third time of the choices
    # are also random
    
    question = sqr.quiz.get_random_question(sqr.cur_quest)
    # From this question, we now choose a random input choice
    a_choice = question.get_random_choice()
    # This choice could either be a tuple of numbers, a randomizer, or a mix. We need to parse these into
    # actual numbers
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
    
    # If the question we grabbed is multiple choice, then we must also generate the multiple choice options.
    if question.q_type == "MC":
        mc_choices = get_mc_choices(question, choices, answer)
        result[qnum].update({'mc_choices': mc_choices})
    
    sqr.update_result(result)

    return get_return_string(question,choices), mc_choices

def get_mc_choices(question, choices, answer):
    """ Given a question and a choice for the variable inputs, get the multiple choice options.
        Input: question (MarkedQuestion)
               choices  (String) corresponding to the concrete choices for the v[0],...,v[n]
               answer   (String) to concatenate to the choices list
        Output: A list of strings with numeric values. For example ['13', '24', '52.3', 'None of the above']
    """
    split_choices = choices.split(';')
    mc_choices = []

    for part in question.mc_choices.replace(' ','').split(';'):
        try:
            if re.findall(r'{v\[\d+\]}', part): # matches no variables
                eval_string = part.format(v=split_choices)
            else:
                eval_string = part #could be an evaluable string, or a sentence
            value = round(simple_eval(eval_string, functions=settings.PREDEFINED_FUNCTIONS,names=settings.UNIVERSAL_CONSTANTS),4)
                
            mc_choices.append(str(value))
        except: #If not an exectuable string, then it must be a hardcoded answer
            mc_choices.append(part)

    mc_choices.append(str(answer))
    random.shuffle(mc_choices)

    # Now shuffle them.
    return mc_choices

def parse_abstract_choice(abstract_choice):
    """ Parses an abstract choice into a concrete choice. Expects a single choice input. Currently can
        only handle integer ranges.
        Input: abstract_choice (String) - Used to indicate an abstract choice, separated by ';'
        Output: (String) A concrete choice 
    """
    choice = ''
    for part in abstract_choice.replace(' ', '').split(';'):
        if isnumber(part): # If already a number
            choice += part + ";"
        else: # it must be a command, one of 'rand' or 'uni'
            pre_choice = simple_eval(part, 
                                 names=settings.UNIVERSAL_CONSTANTS,
                                 functions=settings.PREDEFINED_FUNCTIONS)
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
        Input: question (MarkedQuestion) - the object containing the question
               choices (String) - String containing *concrete* choices
        Return: (Integer) - The answer, to be saved

        Depends: simpleeval.simple_eval
    """
    answer = question.answer
    try:
        # Substitute the variables into the string and evaluate the functions dictionary
        eval_string = answer.format(v=choices.split(';'))
        functions = eval(question.functions)
        functions.update(settings.PREDEFINED_FUNCTIONS)

        return round(simple_eval(eval_string, functions=functions, names=settings.UNIVERSAL_CONSTANTS),4)
    except (SyntaxError, NameNotDefined,) as e:
        # Enter this exception if the answer is not one that can be evaluated.
        # In that case, the answer is just the answer
        if question.q_type == "MC":
            return answer
        else:
            raise e

    except Exception as e: 
        raise e

@login_required
def display_question(request, sqrpk, submit=None):
    """ Shows the current question quiz-question. Is almost a redirect which handles the question.
        Input: sqrpk (integer) - indicating the StudentQuizResult primary key
        Output: HttpResponse - renders the quiz question

        Depends: get_return_string, mark_question, generate_next_question
    """

    sqr = StudentQuizResult.objects.select_related('quiz').get(pk=sqrpk)
    string_answer = ''
    error_message = ''
    mc_choices = None
    # Start by doing some validation to make sure only the correct student has access to this page
    if sqr.student != request.user:
        return HttpResponseForbidden()

    # Just display the current question
    if submit is None:
        result, qnum = sqr.get_result()
        # Asked to display a quiz which has already been finished
        if qnum == '0':
            result_table = get_result_table(sqr.result)
            return render(request, 'Problems/completed_quiz.html', 
                    {   'sqr': sqr,
                        'result_table': result_table,
                    })

        # result[qnum] has fields (MarkedQuestion) pk, inputs, score, type, (mc_choices)
        question = MarkedQuestion.objects.get(pk=int(result[qnum]['pk']))
        choices  = result[qnum]['inputs']
        q_string = get_return_string(question, choices)
        
        if result[qnum]['type'] == "MC":
            mc_choices = result[qnum]['mc_choices']

    else: # We need to mark the question and generate the next question

        if request.method == "GET": # Refreshed the page/sorted the table
            result_table = get_result_table(sqr.result)
            RequestConfig(request, paginate={'per_page', 10}).configure(result_table)
            return render(request, 'Problems/completed_quiz.html', 
                    {   'sqr': sqr,
                        'result_table': result_table,
                    })

        q_string = request.POST['problem'] # Grab this in case we need to return the question on error
        try:
            string_answer = request.POST['answer'] #string input
            is_last       = mark_question(sqr, string_answer)

            if not is_last: # There are more questions, so make the next one
                q_string, mc_choices = generate_next_question(sqr)
                string_answer = ''
            else:
                result_table = get_result_table(sqr.result)
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
            error_message = "The expression '{}' did not parse to a valid mathematical expression. Please try again".format(string_answer)
            # Technically if we get here, we do not have the mc_choices to return if it was a multiple choice
            # question; however, this should never happen as it should be impossible to pass a bad input with mc

    return render(request, 'Problems/display_question.html', 
            {'sqr': sqr,
             'question': q_string, 
             'sqrpk': sqrpk,
             'error_message': error_message,
             'string_answer': string_answer,
             'mc_choices': mc_choices,
             })

def get_result_table(result):
    """ Turns the (string) StudentQuizResults.results into a table.
    """
    
    ret_data = []
    res_dict = json.loads(result)
    for field, data in res_dict.items():
        part = {'q_num': field, 
                'correct': str(data['answer']), 
                'guess': str(data['guess']),
                'score': data['score']}
        ret_data.append(part)
    
    return QuizResultTable(ret_data)

@staff_required()
def test_quiz_question(request, mpk):
    """ Generates many examples of the given question for testing purpose.
        Input: mpk (Integer) MarkedQuestion primary key
    """
    mquestion = get_object_or_404(MarkedQuestion, pk=mpk)

    if request.method == "POST":
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

                problem = get_return_string(mquestion, choice)
                
                html += render_html_for_question(problem, answer, choice, mc_choices)
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
               <div class = "diff quiz-divs question-detail">
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
