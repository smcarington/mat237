from django.contrib import admin
from .models import ProblemSet, Question, QuestionStatus, Announcement, Poll, PollQuestion, PollChoice, LinkedDocument, DocumentCategory

# Register your models here.
admin.site.register(ProblemSet)
admin.site.register(Question)
admin.site.register(QuestionStatus)
admin.site.register(Announcement)
admin.site.register(Poll)
admin.site.register(PollQuestion)
admin.site.register(PollChoice)
admin.site.register(LinkedDocument)
admin.site.register(DocumentCategory)
