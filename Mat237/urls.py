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
from django.conf.urls import url, include, patterns
from django.contrib.auth.views import login, logout, password_change, password_change_done
from django.contrib import admin

urlpatterns = [
    url(r'^superuser/', admin.site.urls),
    url(r'^Problems/', include('Problems.urls')),
    url(r'^accounts/login/$', login, name='login'),
    url(r'^accounts/logout/$', logout, {'next_page': '/Problems/'}, name='logout'),
    url(r'^accounts/password_change/$', password_change, {'template_name': 'registration/password_change.html', 'post_change_redirect': 'announcements'}, name='password_change'),
    url(r'^accounts/password_change/done/$', password_change_done, name='password_change_done'),
]
