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
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib.auth.views import (login, logout, password_change,
    password_change_done, password_reset, password_reset_done,
    password_reset_confirm, password_reset_complete)
from django.contrib import admin

url_prepend = settings.URL_PREPEND
import accounts.views as account_views

urlpatterns = [
    url(r'^tholden/login/$', account_views.remote_login, name='remote_login'),
    url(r'^{prepend}superuser/'.format(prepend=url_prepend), admin.site.urls),
    url(r'^{prepend}accounts/'.format(prepend=url_prepend),
        include('accounts.urls')),
    url(r'^{prepend}'.format(prepend=url_prepend), include('Problems.urls')),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
