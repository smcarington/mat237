from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from datetime import timedelta

import re

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
    solution   = models.TextField(default='');

# Localtime function to pass to DateTimeField callable
def get_localtime():
    return timezone.localtime(timezone.now())

# For staff to make announcements
class Announcement(models.Model):
    author   = models.ForeignKey(User)
    title    = models.CharField(max_length=30)
    text     = models.TextField()
    stickied = models.BooleanField(default=False)

    created_date   = models.DateTimeField(default=get_localtime)
    published_date = models.DateTimeField(
                        blank=True, null=True)
    expires        = models.DateField(blank=True, null=True, default=timezone.now()+timedelta(days=7))

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
        """.format(extra=stclass, title=sticktitle, date=timezone.localtime(self.published_date).strftime("%A, %B %d, %I:%M%p"), text=self.text, author=full_name)

    def __str__(self):
        return self.title

class Poll(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title

class PollQuestion(models.Model):
    poll     = models.ForeignKey(Poll)
    text     = models.TextField(blank=True,null=True)
    live     = models.BooleanField(default=False)
    num_poll = models.IntegerField(default=1)
    visible  = models.BooleanField(default=False)
    can_vote = models.BooleanField(default=False)
    position = models.IntegerField(default=0)

    # Called when an administrator pushes the poll to the live page. View handles
    # setting all other visibility settings to false
    def start(self):
        self.visible  = True
        self.can_vote = True
        self.save()

    def stop(self):
        self.can_vote = False
        self.save()

    def reset(self):
        # Clone the choices, update cur_poll and num_poll. Returns a dictionary
        # item containing the map of primary keys
        clones = self.pollchoice_set.filter(cur_poll=self.num_poll).order_by('id')
        self.num_poll = self.num_poll+1
        self.save()

        # By setting the clone pk=None, the save method creates a new instance of the model.
        # We must still manually reset the number of votes though. In addition, for the change
        # in the poll-admin page, we need to return a map of how the primary keys have changed.
        pk_map = {}
        for clone in clones:
            old_pk = str(clone.pk)

            # Reset the clone
            clone.cur_poll = self.num_poll
            clone.pk = None
            clone.num_votes = 0
            clone.save()

            # Get the new pk and add it to the pk_map
            new_pk = str(clone.pk)
            pk_map[old_pk]=new_pk

        return pk_map

    def move_position(self, direction):
        """ Change the position of a PollQuestion item. Handles the problem of 
            changing neighbouring position numbers as well. 
            Input : direction - A (String) indicating either 'up' or 'down'.
            Output: status - An integer indicating the success state.
                             -2 ~ no neighbouring object
                              1 - success
        """
        # Grab the neighbour. Throw an appropriate error.
        cur_pos = self.position
        try:
            if direction == "up":
                # neighbour = PollQuestion.objects.get(poll=self.poll,position=cur_pos-1)
                # To more easily deal with deletions, instead of reseting the positions on 
                # deletion, just get the nearest neighbour. Do this by getting all questions
                # with higher position, and ordering them so that the closest is in the first position.

                neighbours = PollQuestion.objects.filter(poll=self.poll, position__lt=cur_pos).order_by('-position')
                if len(neighbours)==0:
                    return -2
            elif direction == "down":
                # neighbour = PollQuestion.objects.get(poll=self.poll,position=cur_pos+1)
                neighbours = PollQuestion.objects.filter(poll=self.poll, position__gt=cur_pos).order_by('position')
                if len(neighbours)==0:
                    return -2
        except PollQuestion.DoesNotExist:
                return -2

        neighbour = neighbours[0]
        
        self.position = neighbour.position
        neighbour.position = cur_pos

        self.save()
        neighbour.save()

        return 1

    def __str__(self):
        return "Poll {number}: {text}".format(number=self.poll.pk, text=self.text[0:20])

class PollChoice(models.Model):
    question  = models.ForeignKey(PollQuestion)
    text      = models.CharField(max_length=400)
    num_votes = models.IntegerField(default=0)
    cur_poll  = models.IntegerField(default=1)

    class Meta:
        ordering = ['pk']

    def add_vote(self):
        self.num_votes = self.num_votes+1
        self.save()

    def __str__(self):
        return self.text

# User uploads go to a special file in MEDIA_ROOT
def content_file_name(instance, filename):
    return '/'.join(['content', filename])

class DocumentCategory(models.Model):
    cat_name = models.CharField(max_length=100)

    def __str__(self):
        return self.cat_name

class LinkedDocument(models.Model):
    link_name = models.CharField(max_length=200)
    category  = models.ForeignKey(DocumentCategory, null=True, related_name="docs")
    user      = models.ForeignKey(User)
    doc_file  = models.FileField()

    def __str__(self):
        return self.user.username + ' ' + self.doc_file.name

class Quiz(models.Model):
    name    = models.CharField(max_length=200)
    # Number of tries a student is allowed. A value of category=0 is equivalent to infinity.
    tries   = models.IntegerField(default=0)
    live    = models.DateTimeField()
    expires = models.DateTimeField()
    out_of  = models.IntegerField(default=1)

    # Determines how many questions are in the current quiz.
    def update_out_of(self):
        self.out_of = self.markedquestion_set.count()
        self.save()

    def __str__(self):
        return self.name

class MarkedQuestion(models.Model):
    quiz        = models.ForeignKey("Quiz", Quiz, null=True)
    # Keeps track of the global category, so that multiple questions can be used
    category    = models.IntegerField("Category", default=1)
    problem_str = models.TextField("Problem")
    choices     = models.TextField("Choices", null=True)
    num_vars    = models.IntegerField(null=True)

    class Meta:
        ordering = ['quiz', 'category']

    def update(self, quiz):
        self.quiz = quiz
        self.num_vars = len(re.findall(r'{v\[\d+\]}', self.problem_str))
        self.save()

    def __str__(self):
        return self.problem_str

class StudentQuizResult(models.Model):
    student   = models.ForeignKey(User)
    quiz      = models.ForeignKey(Quiz)
    attempt   = models.IntegerField(null=True) #track which attempt this is
    #track which question the student is on if they leave. If cur_question = 0 then completed
    cur_quest = models.IntegerField(null=True) 

    # The result is a json string which serializes the question data. For example
    # result = {
    #           '13': {
    #                   'inputs': [1,2,3], 
    #                   'score': '0'
    #                 },
    #           '52': {
    #                   'inputs': [8,-2], 
    #                   'score': '1'
    #                 },
    #          }
    #          Indicates that the first question is a MarkedQuestion with pk=13, the inputs to
    #          this question were v=[1,2,3], and the student got the question wrong
    result  = models.TextField()
    score   = models.IntegerField(null=True)

    def __str__(self):
        return self.user.username + self.quiz.name + self.score
