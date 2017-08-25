from django.shortcuts import render, redirect

def remote_login(request):
    """ Used to redirect to the desired page after loggin in. Wherever login is
    directed should be protected by the remote user.
    """
    if request.user.is_authenticated():
        next_page = request.GET['next']
        return redirect(next_page)
    else:
        return render(request, 'accounts/not_authorized.html')
