from django.contrib import admin
from .models import ProblemSet, Question, QuestionStatus, Announcement

# Register your models here.
admin.site.register(ProblemSet)
admin.site.register(Question)
admin.site.register(QuestionStatus)
admin.site.register(Announcement)
