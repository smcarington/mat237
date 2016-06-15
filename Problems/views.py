from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.views import password_change
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail, EmailMessage
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import Max

import json
import subprocess
import os
import re

from django.contrib.auth.models import User
from .models import Announcement, ProblemSet, Question, QuestionStatus, Poll, PollQuestion, PollChoice, LinkedDocument
from .forms import AnnouncementForm, QuestionForm, ProblemSetForm, NewStudentUserForm, PollForm, LinkedDocumentForm, TextFieldForm

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
    docs = LinkedDocument.objects.all()
    return render(request, 'Problems/notes.html', {'docs':docs})

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

        choice.add_vote()
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
            print(e)

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

## ----------------- HISTORY ----------------------- ## 

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
