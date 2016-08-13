"""Mat237 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from django.conf import settings
from django.conf.urls import url, include, patterns
from django.conf.urls.static import static
from django.contrib.auth.views import login, logout, password_change, password_change_done
from django.contrib import admin

url_prepend = settings.URL_PREPEND

urlpatterns = [
    url(r'^{prepend}superuser/'.format(prepend=url_prepend), admin.site.urls),
    url(r'^{prepend}accounts/login/$'.format(prepend=url_prepend), login, name='login'),
    url(r'^{prepend}accounts/logout/$'.format(prepend=url_prepend), logout, {'next_page': '/'}, name='logout'),
    url(r'^{prepend}accounts/password_change/$'.format(prepend=url_prepend), password_change, {'template_name': 'registration/password_change.html', 'post_change_redirect': 'announcements'}, name='password_change'),
    url(r'^{prepend}accounts/password_change/done/$'.format(prepend=url_prepend), password_change_done, name='password_change_done'),
    url(r'^{prepend}'.format(prepend=url_prepend), include('Problems.urls')),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
