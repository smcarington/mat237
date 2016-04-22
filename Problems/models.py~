from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Problem sets and questions. Note that questions should be
# Many2One.

class ProblemSet(models.Model):
    title   = models.CharField(max_length=20)
    visible = models.BooleanField(default=True)

class Question(models.Model):
    DIFF_CHOICES = (
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
        ('I', 'Impossible'),
    )
    problem_set = models.ForeignKey(ProblemSet, related_name = 'problems')
    text        = models.TextField()
    difficulty  = models.CharField(max_length=1, choices=DIFF_CHOICES, default='E');

class QuestionStatus(models.Model):
    STUD_DIFF_CHOICES = [(i,i) for i in range(1,11)]
    user       = models.ForeignKey(User, related_name = 'question_status')
    question   = models.ForeignKey(Question)
    attempt    = models.BooleanField(default=False)
    solved     = models.BooleanField(default=False)
    difficulty = models.IntegerField(choices=STUD_DIFF_CHOICES)

# For staff to make announcements
class Announcement(models.Model):
    author   = models.ForeignKey(User)
    title    = models.CharField(max_length=30)
    text     = models.TextField()
    stickied = models.BooleanField(default=False)
    created_date   = models.DateTimeField(
                        default=timezone.now)
    published_date = models.DateTimeField(
                        blank=True, null=True)
    expires        = models.DateTimeField(blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title
