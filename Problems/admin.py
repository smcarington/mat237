from django.contrib import admin
from .models import (ProblemSet, Question, QuestionStatus, Announcement, Poll,
PollQuestion, PollChoice, LinkedDocument, DocumentCategory, StudentVote, Quiz,
MarkedQuestion, StudentQuizResult, Evaluation, StudentDocument, Typo,
StudentMark, StudentInfo, Tutorial, CSVBackup)

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
admin.site.register(StudentVote)
admin.site.register(Quiz)
admin.site.register(MarkedQuestion)
admin.site.register(StudentQuizResult)
admin.site.register(Evaluation)
admin.site.register(StudentDocument)
admin.site.register(Typo)
admin.site.register(StudentMark)
admin.site.register(StudentInfo)
admin.site.register(Tutorial)
admin.site.register(CSVBackup)
