from django.conf.urls import url, include, patterns
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.post_announcements, name='announcements'),
    url(r'^problemSet/(?P<pk>\d+)/', views.list_problem_set, name='list_problem_set'),
    url(r'^question/(?P<pk>\d+)/', views.question_details, name='question_details'),
    url(r'^announcement/new/', views.new_announcement, name='new_announcement'),
    url(r'^syllabus/', views.syllabus, name='syllabus'),
    url(r'^calendar/', views.calendar, name='calendar'),
    url(r'^administrative/', views.administrative, name='administrative'),
]
