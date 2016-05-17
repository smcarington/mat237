from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.views import password_change
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail

import json

from django.contrib.auth.models import User
from .models import Announcement, ProblemSet, Question, QuestionStatus, Poll, PollQuestion, PollChoice
from .forms import AnnouncementForm, QuestionForm, ProblemSetForm, NewStudentUserForm, PollForm

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

def syllabus(request):
    return render(request, 'Problems/syllabus.html')

@login_required
def calendar(request):
    return render(request, 'Problems/calendar.html')

@login_required
def notes(request):
    return render(request, 'Problems/notes.html')

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
    questions = poll.pollquestion_set.all()

    return render(request, 'Problems/list_pollquestions.html', {'questions': questions, 'poll': poll})

# Only handles rendering the poll admin page. AJAX requests handled by other views
@staff_required()
def poll_admin(request, pollpk):
    poll = get_object_or_404(Poll, pk=pollpk)
    return render(request, 'Problems/poll_admin.html', {'poll': poll})

@staff_required()
def new_pollquestion(request, pollpk, questionpk=None):
# To facilitate question + choice at the same time, we must instantiate the
# question before hand. This will also make editing a question easy in the
# future

    poll = get_object_or_404(Poll, pk=pollpk)

    # If a question is created for the first time, we must instantiate it so that
    # our choices have somewhere to point. If it already exists, retrieve it
    if questionpk is None:
        question = PollQuestion(poll=poll)
        question.save()
    else:
        question = get_object_or_404(PollQuestion, pk=questionpk)

    # The form has been submitted. We need to create the appropiate database models.
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
        return render(request, 'Problems/new_pollquestion.html', {'question': question, 'choices': choices})


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
        if status == 'start':
            PollQuestion.objects.filter(visible=True).update(visible=False, can_vote=False)
            question.start()
            response_data = {'response': 'Question pushed to live page'}
        elif status == 'stop':
            if not question.can_vote:
                response_data = {'response': 'No question to stop'}
            else:
                question.stop()
                response_data = {'response': 'Question stopped. Displaying results.'}
            # Need to do some computations here to return data
        elif status == 'reset':
            if not question.visible:
                response_data = {'response': 'That question is not visible'}
            else:
                question.reset()
                response_data = {'response': 'Data saved. Reopening the vote'}
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
        except:
            response_data = {'state': "-1"}

    return HttpResponse(json.dumps(response_data))

## ----------------- PDFLATEX -----------------------##

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
        import pdb; pdb.set_trace() 
        for item in questions:
            qpk       = int(item['number'])
            
            # Grab the question, as well as the QuestionStatus object for that question
            # corresponding to the given user
            quest    = get_object_or_404(Question, pk=qpk)
            stud_sol = quest.status.filter(user=user)
            text     = quest.text

            if quest['sol']:
                sol_text = stud_sol.solution
            else:
                sol_text = ''

            qlist.push([text, sol_text])

        # Send the data to a helper function to add the pre-amble. Returns a string which
        # we will make into a file for compiling
        latex_source = create_latex_source(qlist)
        # Send the file to be compiled and emailed using another helper function
        compile_and_email(latex_source, user)

    else:
        raise Http404('Request not posted')

def create_latex_source(question_list):
    """ A helper function for the function 'pdflatex'. Accepts a list of questions and
        their solutions and assembles the appropriate latex file. 
        Input: question_list - a 2d array who's 0-argument is the question text and
                   whose 1-argument is the solution text (possibly empty)
        Out  : (string) with the full pdf source code
    """
    pass

def compile_and_email(latex_source, user):
    """ A helper function for the function 'pdflatex'. Accepts a string with the full latex
        source code. Creates a file with this string, compiles it, and emails it to the user.
        Input: latex_source - A (string) containing the latex source code.
               user         - (User) element corresponding to session user.
        Out  : A (string) indicating the success/failure of the method.
    """
    pass
