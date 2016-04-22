from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from .models import Announcement

# Create your views here.

# @login_required
def post_announcements(request):
    posts = Announcement.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'Problems/post_announcements.html', {'posts': posts})

#@login_required
#def post_new(request):
#    if request.method == "POST":
#        form = AnnouncementForm(request.POST)
#        if form.is_valid():
#            post = form.save(commit=False)
#            post.author = request.user
#            post.save()
#            return redirect('post_detail', pk=post.pk)
#    else:
#        form = AnnouncementForm()
#
#    return render(request, 'Problems/post_edit.html', {'form' : form})

@login_required
def post_draft_list(request):
    posts = Announcement.objects.filter(published_date__isnull=True).order_by('created_date')
    return render(request, 'Problems/post_draft_list.html', {'posts': posts})

@login_required
def post_publish(request, pk):
    post = get_object_or_404(Announcement, pk=pk)
    post.publish()
    return redirect('post_detail', pk=pk)

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Announcement, pk=pk)
    post.delete()
    return redirect('post_list')
