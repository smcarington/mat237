from django.conf.urls import url, include, patterns
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.post_announcements, name='announcements'),
]
