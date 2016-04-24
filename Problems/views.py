from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import password_change

from .models import Announcement
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

