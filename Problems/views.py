from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import password_change

from .models import Announcement, ProblemSet, Question, QuestionStatus
from .forms import AnnouncementForm

# Create your views here.

# @login_required
def post_announcements(request):
    posts = Announcement.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    return render(request, 'Problems/post_announcements.html', {'announcements': posts})

@login_required
@permission_required('Can add announcement')
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

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Announcement, pk=pk)
    post.delete()
    return redirect('post_list')

@login_required
def syllabus(request):
    return render(request, 'Problems/syllabus.html')

@login_required
def calendar(request):
        return render(request, 'Problems/calendar.html')

@login_required
def administrative(request):
            return render(request, 'Problems/administrative.html')

@login_required
def list_problem_set(request, pk):
    ps = get_object_or_404(ProblemSet, pk=pk)

    # There is no standary sort_by on the charfield that returns difficulty, so we use the 'extra' method
    CASE_SQL = '(case when difficulty="E" then 1 when difficulty="M" then 2 when difficulty="H" then 3 when difficulty="I" then 4 end)'
    problems = ps.problems.extra(select={'difficulty': CASE_SQL}, order_by=['difficulty'])
    return render(request, 'Problems/list_problem_set.html', {'problems': problems, 'problem_set': ps})

def question_details(request, pk):
    problem = get_object_or_404(Question, pk=pk)
    problemStatus, created = QuestionStatus.objects.get_or_create(user=request.user, question=problem)

    if request.method == "POST":
        solution = request.POST['solution']
        problemStatus.solution = solution
        problemStatus.save()

    return render(request, 'Problems/question_details.html', {'problem': problem, 'status': problemStatus})

@login_required
def update_status(request):
    try:
        user     = get_object_or_404(User, pk=request.POST['user'])
        question = get_object_or_404(Question, pk=request.POST['question'])
        status   = get_object_or_404(QuestionStatus, user=user, question=question)

        status.attempt = 
