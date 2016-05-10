from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from datetime import timedelta

# Problem sets and questions. Note that questions should be
# Many2One.

class ProblemSet(models.Model):
    title   = models.CharField(max_length=20)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.title;

class Question(models.Model):
    DIFF_CHOICES = (
        (1, 'Easy'),
        (2, 'Medium'),
        (3, 'Hard'),
        (4, 'Impossible'),
    )
    problem_set = models.ForeignKey(ProblemSet, related_name = 'problems')
    text        = models.TextField()
    difficulty  = models.IntegerField(choices=DIFF_CHOICES, default=1);
    attempts    = models.IntegerField(default=0)
    solved      = models.IntegerField(default=0)
    stud_diff   = models.IntegerField(default=1)

    def __str__(self):
        return self.text[0:20]

class QuestionStatus(models.Model):
    STUD_DIFF_CHOICES = [(i,i) for i in range(1,11)]
    user       = models.ForeignKey(User, related_name = 'question_status')
    question   = models.ForeignKey(Question, related_name = 'status')
    attempt    = models.BooleanField(default=False)
    solved     = models.BooleanField(default=False)
    difficulty = models.IntegerField(choices=STUD_DIFF_CHOICES, default=1)
    solution   = models.TextField(blank=True);

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
    expires        = models.DateField(blank=True, null=True, default=timezone.now()+timedelta(days=21))

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def as_html(self):
        sticktitle = self.title
        stclass = ''
        if self.stickied:
            sticktitle = self.title + "&#42;"
            stclass    = ' sticky'

        full_name = self.author.first_name +" " + self.author.last_name

        return """
            <div class="diff announcement{extra}">
                <div class="row ann-title">
                    <div class = "col-sm-4">
                        <h4>{title}</h4>
                    </div>
                    <div class = "col-sm-4">
                        
                    </div>
                    <div class = "col-sm-4">
                        <small><emph> Posted: {date}</emph> </small>
                    </div>
                </div>

                <div class="row ann-text">
                    <div class = "col-sm-12">
                        <p>{text}</p>
                    </div>
                </div>

                <div class = "row ann-author">
                    <div class = "col-sm-8">
                    </div>
                    <div class = "col-sm-4">
                        <p>Published by: {author}</p>
                    </div>
                </div>
            </div>
        """.format(extra=stclass, title=sticktitle, date=self.published_date.strftime("%A, %B %d, %I:%M%p"), text=self.text, author=full_name)

    def __str__(self):
        return self.title

class Poll(models.Model):
    title = models.CharField(max_length=200)

class PollQuestion(models.Model):
    poll = models.ForeignKey(Poll)
    text = models.TextField(blank=True,null=True)
    live = models.BooleanField(default=False)

class PollChoice(models.Model):
    question = models.ForeignKey(PollQuestion)
    text     = models.CharField(max_length=200)
