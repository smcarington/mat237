from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Max
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from datetime import timedelta

import re
import json
import random

from .validators import FileValidator

# Problem sets and questions. Note that questions should be
# Many2One.

# --- Problem Set (fold) --- #

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
    solution    = models.TextField(default='', blank=True)

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

def get_time():
    return timezone.now()+timedelta(days=7)

# For staff to make announcements
class Announcement(models.Model):
    author   = models.ForeignKey(User)
    title    = models.CharField(max_length=30)
    text     = models.TextField()
    stickied = models.BooleanField(default=False)

    created_date   = models.DateTimeField(default=get_localtime)
    published_date = models.DateTimeField(
                        blank=True, null=True)
    expires        = models.DateTimeField(blank=True, null=True, default=get_time)

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
                    <div class = "col-sm-8">
                        <h4>{title}</h4>
                    </div>
                    <div class = "col-sm-4">
                        <p class="posted"> Posted: {date}</p>
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

# --- Problem Set (end) --- #

# --- Classroom Response (fold) --- #

class Poll(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title

class PollQuestion(models.Model):
    poll     = models.ForeignKey(Poll)
    text     = models.TextField(blank=True)
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
        try:
            return "Poll {number}: {text}".format(number=self.poll.pk, text=self.text[0:20])
        except Exception as e:
            return "Error"


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

    def sub_vote(self):
        if self.num_votes == 0:
            raise Exception('Already zero votes')
        else:
            self.num_votes = self.num_votes-1
            self.save()

    def __str__(self):
        return self.text

class StudentVote(models.Model):
    student  = models.ForeignKey(User)
    question = models.ForeignKey(PollQuestion, null=True)
    vote     = models.ForeignKey(PollChoice, related_name="votes", null=True)
    cur_poll = models.IntegerField(default=1)

    #class Meta:
    #    unique_together = ('student', 'question', 'cur_poll')

    def add_choice(self, choice):
        """ In a new vote, and the choice, save it, and increment the PollChoice object
            Input: vote (PollChoice) - The choice to add to the StudentVote element
            Return: void
        """
        self.vote = choice;
        self.save()
        choice.add_vote()

    def change_vote(self, new_vote):
        """ Changes the vote element.
            Input: new_vote (PollChoice) - The new vote
            Return: void
        """

        old_vote = self.vote
        old_vote.sub_vote() 
        # Now that we've remove the last vote, we change the vote element and update it's count
        self.vote = new_vote
        self.save()
        new_vote.add_vote()

    def __str__(self):
        return self.student.username + ' vote '

# User uploads go to a special file in MEDIA_ROOT
def content_file_name(instance, filename):
    return '/'.join(['content', filename])

# --- Classroom Response (end) --- #

# --- Marks and Notes (fold) --- #

class DocumentCategory(models.Model):
    cat_name = models.CharField(max_length=100)

    def __str__(self):
        return self.cat_name

def directory_setter(instance, filename):
    if hasattr(instance, 'evaluation'):
        join_path = settings.NOTE_ROOT
    else:
        join_path = 'document'
    return '/'.join([join_path, instance.doc_file.name])

class Evaluation(models.Model):
    """ Model used to track events to which students might need evaluation . Is
        badly named, since it is also used as model for storing StudentMark
        categories, such as tests and quizzes.

        To Do: Rename 
    """
    name = models.CharField(max_length=200)
    out_of = models.IntegerField(default=0)

    def quiz_update_out_of(self, quiz):
        """ If the evaluation corresponds to a quiz, we update the out_of category
        """
        self.out_of = quiz.out_of
        self.save()

    def __str__(self):
        return self.name

def note_name_setter(instance, filename):
    """ Creates the appropriate filename 
    """
    return "{user}_{evaluation}_{filename}".format(user     = instance.user.username, 
                                                  evaluation= instance.evaluation.name, 
                                                  filename = filename)

class UserDocument(models.Model):
    """ Abstract model field for instructor-uploaded documents. Used for
        linked-documents and CSVBackup
    """
    user     = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_related")
    validate_file = FileValidator(content_types=('application/pdf',
                                                 'image/jpeg',
                                                 'image/png',
                                                 'text/plain',)
                                 )
    doc_file = models.FileField(upload_to=directory_setter,
                                validators=[validate_file]
                               )
    class Meta:
        abstract = True

class LinkedDocument(UserDocument):
    """ Used for instructor-uploaded documents. Will appear in /notes section of
        website. 
        To Do: Make visible/invisible.
    """
    link_name = models.CharField(max_length=200)
    category  = models.ForeignKey(DocumentCategory, null=True, related_name="docs")
    live_on   = models.DateTimeField(blank=True, null=True, default=timezone.now)

    def is_live_now(self):
        """ Used to check if the document is currently visible """
        return self.live_on < timezone.now()

    def __str__(self):
        return "Public link. Uploaded: " + self.user.username + ' Doc Name: ' + self.doc_file.name

class CSVBackup(UserDocument):
    """ Inherits UserDocument. Used for storing CSV files, whether user uploaded
        or the backup for a grade change.
    """
    file_name = models.CharField(max_length=200)
    category  = models.ForeignKey(Evaluation, null=True, blank=True)

    def set_user_and_name(self, the_user):
        """ Model method for setting the user. Will automatically save."""
        self.user = the_user

        # We name the file according to the uploading user and the timestamp
        the_time = timezone.now().date()
        the_name = "{user}_{doc_name}_{timestamp}".format(user=the_user,
                doc_name=self.doc_file.name, timestamp=the_time)
        self.file_name = the_name
        self.save()

    def __str__(self):
        return self.file_name

# Tempting to inherit from user document, but tricker since we need storage to be secure
class StudentDocument(models.Model):
    """ Used to allow students to upload files to the website, which only they
        and the instructors are capable of seeing. Used for SickNotes.
    """
    user     = models.ForeignKey(User, related_name='notes')
    validate_file = FileValidator(max_size=1024*1000, 
                                  content_types=('application/pdf',
                                                 'image/jpeg',
                                                 'image/png',)
                                 )
    fs = FileSystemStorage(location=settings.NOTE_ROOT)
    doc_file = models.FileField(upload_to = note_name_setter,
                                storage   = fs,
                                validators=[validate_file]
                               )
    evaluation = models.ForeignKey(Evaluation)
    uploaded = models.DateTimeField(default=timezone.now)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return "Student Note. Uploaded by: " + self.user.username + ', For:' + self.evaluation.name

    def update_user(self, user):
        self.user = user
        self.uploaded = timezone.now()
        self.save()

    def change_accepted(self, boolean):
        self.accepted = boolean
        self.save()

# --- Marks and Notes (end) --- #

# --- Quizzes (fold) --- #

class Quiz(models.Model):
    """ Container for holding a quiz. Quizzes consist of several MarkedQuestion
        objects. In particular, a Quiz object has the following attributes:
        name - (CharField) the name of the quiz
        tries - (IntegerField) The number of attempts a student is permitted to
            for the quiz. A value of tries=0 means unlimited attempts
        live  - (DateTimeField) The date on which the quiz becomes available to
            students
        expires - (DateTimeField) The date on which the quiz closes. 
        _cat_list - (TextField) Contains the category pool numbers. Has custom
            set/get methods to serialize the data.
        out_of - (IntegerField) The number of different MarkedQuestion pools. 
    """
    name    = models.CharField("Name", max_length=200)
    # Number of tries a student is allowed. A value of category=0 is equivalent to infinity.
    tries   = models.IntegerField("Tries", default=0)
    live    = models.DateTimeField("Live on")
    expires = models.DateTimeField("Expires on")
    _cat_list = models.TextField(null=True)
#    # Replaced as a property computed from _cat_list
#    out_of  = models.IntegerField("Points", default=1)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    # cat_list needs custom set/get methods to handle serialization
    @property
    def cat_list(self):
        return self._cat_list

    @cat_list.setter
    def cat_list(self, value):
        """ Sets the _cat_list attribute. value should be a list of integers
            indexing the category pools.
        """
        self._cat_list = json.dumps(value)
        self.save()

    @cat_list.getter
    def cat_list(self):
        return json.loads(self._cat_list)

    # The out_of field is now replaced by a property, equivalent to the number
    # of distinct category numbers
    @property
    def out_of(self):
        return len(self.cat_list)

    def update_out_of(self):
        """ Determines the number of MarkedQuestion pools in this quiz. Is
            called when MarkedQuestions are added/edited/deleted from the quiz.
        """
        cats = list(self.markedquestion_set.all().values_list('category', flat=True))
        # Make distinct
        cats = list(set(cats))
        self.cat_list = cats
        # Old technique,  before allowing for random question order
        # -- Important to base this on the max category, rather than number of questions
        # -- self.out_of = self.markedquestion_set.aggregate(Max('category'))['category__max']
        self.save()

    def get_random_question(self, index):
        """ Returns a random question from the category corresponding to
            cat_list[index]
            <<INPUT>>
            index (integer) - a non-negative integer no more than self.out_of.
                The quiz has an array enumerating the categories, and we pull a
                question from the category corresponding to index. For example,
                if cat_list = [1, 3, 4, 10] and index = 3, we choose a question
                from category=cat_list[index] = cat_list[3] = 10.
            <<OUTPUT>>
            (MarkedQuestion) The question.
        """
        # Get the category list and select the Marked Questions corresponding to
        # this category
        cat_list = self.cat_list
        marked_questions = self.markedquestion_set.filter(
                category=cat_list[index])
        return random.choice(marked_questions)

    def __str__(self):
        return self.name

class MarkedQuestion(models.Model):
    """ An instance of a question within a Quiz object. These are designed to
        have randomized inputs, and additionally can be assigned to a
        MarkedQuestion pool. For example, if three questions all belong to the
        same pool, then when a quiz is created, only one of these three
        questions will be chosen.
        quiz - (ForeignKey[Quiz]) The quiz to which the MarkedQuestion belongs
        category (IntegerField) The MarkedQuestion pool
        problem_str - (TextField) The question itself. Generated variables
            should be the form {v[0]}, {v[1]},..., etc. Should take LaTeX with
            delimiters \( \), though this looks horrific when escaped.
        num_vars - (IntegerField) Keeps track of the number of variables within
            the question
        choices - (TextField) The range that the variables are allowed to take
            on. Delimited by a colon.
        answer - (TextField) The correct answer. Should include {v[0]}, {v[i]}
            as well.
        functions - (TextField) User defined functions.
        q_type - (CharField) Can either be direct entry 'D' (student puts in a
            number) or multiple choice 'MC'. True/False is deprecated as it can
            be created with MC.
        mc_choices - (TextField) Used only when q_type = 'MC', and includes the
           multiple choice answers. These can include variables {v[i]} as well,
           and are delimited by a semi-colon.
    """
    quiz         = models.ForeignKey("Quiz", Quiz, null=True)
    # Keeps track of the global category, so that multiple questions can be used
    category     = models.IntegerField("Category", default=1)
    problem_str = models.TextField("Problem")
    choices      = models.TextField("Choices", null=True)
    num_vars     = models.IntegerField(null=True)
    answer       = models.TextField("Answer")
    functions    = models.TextField("Functions", default='{}')
    # Allows for multiple kinds of questions
    QUESTION_CHOICES = ( 
            ('D', 'Direct Entry'),
            ('MC', 'Multiple Choice'),
            ('TF', 'True/False'),
        )

    q_type      = models.CharField("Question Type",
                    max_length=2, 
                    choices=QUESTION_CHOICES,
                    default='D',
                  )
    mc_choices = models.TextField("Multiple Choice", default ='[]', blank=True)

    class Meta:
        ordering = ['quiz', 'category']
        verbose_name = "Marked Question"

    def save(self, *args, **kwargs):
        """ Override save so that set_num_vars is called automatically"""
        self.set_num_vars()
        super(MarkedQuestion, self).save(*args, **kwargs)

    # Whenever we set the problem_str, this function is called to update the
    # number of variables. It also validates that they are sequentially indexed
    def set_num_vars(self):
        """ Go through problem_str and check the variables {v[i]}. Ensure the
            'i' occur in sequential order, and throw an error otherwise
        """
        # Use a regex to find all instances of {v[i]}, but only capture the
        # variable indices. 
        list_of_vars = re.findall(r'{v\[(\d+)\]}', self.problem_str)
        # Find the distinct indices, convert them to integers, and sort
        list_of_vars = list(set(list_of_vars))
        list_of_vars = [int(var_ind) for var_ind in list_of_vars]
        list_of_vars = sorted(list_of_vars)
        # Now we check whether they are sequential
        if all(a==b for a,b in enumerate(list_of_vars, list_of_vars[0])):
            self.num_vars = len(list_of_vars)
        else:
            self.num_vars = None
            raise NonSequentialVariables(
                "Variables have non-sequential indices {}".format(list_of_vars)
            )

    def update(self, quiz):
        """ Updates the quiz to which this belongs, and updates that quiz's
            attributes as well. Called when adding/editing/deleting a
            MarkedQuestion.
        """
        self.quiz = quiz
        self.save()
        quiz.update_out_of()

    def get_random_choice(self):
        """ Returns a random choice"""
        return random.choice(self.choices.split(':'))

    def __str__(self):
        return self.problem_str

class StudentQuizResult(models.Model):
    """ When a student starts/writes a quiz, it creates a StudentQuizResult
        instance. This tracks which questions were generated in the quiz, which
        choices for the variables were made, how the student answered (both the
        direct input and how it was evaluated). 
        <<Attributes>>
        student - (ForeignKey[User]) The student who wrote the quiz
        quiz    - (ForeignKey[Quiz]) The quiz the student wrote
        attempt - (IntegerField) Which attempt does this StudentQuizResult
            correspond to.
        cur_quest - (IntegerField) This object is updated each time the student
            completes a question. This tracks which question the student is on,
            allowing the student to leave during a quiz and resume again later.
        result - (TextField) String serialized as a JSON object. 
        score - (IntegerField) The score the student achieved in this question.
        _q_order - (Private: JSON serialized list) A randomization of the array
            [0,1,2,...,quiz.out_of-1] indicating the order of indices to pull 
            from quiz.cat_list. Allows for non-sequential ordering of
            categories. For example, if 
                quiz.cat_list = [1, 3, 4, 10*]
                quiz.out_of   = 4
                _q_order      = [1, 0, 3, 2*]
            then question cur_quest = 4 corresponds to
            pool = cat_list[_q_order[cur_quest-1]] = cat_list[_q_order[3]] 
                 = cat_list[2] = 10.
    """
    student   = models.ForeignKey(User)
    quiz      = models.ForeignKey(Quiz)
    attempt   = models.IntegerField(null=True, default=1) #track which attempt this is
    #track which question the student is on if they leave. If cur_question = 0 then completed
    cur_quest = models.IntegerField(null=True, default=1) 

    # The result is a json string which serializes the question data. For example
    # result = {
    #           '1': {
    #                   'pk': '13',
    #                   'inputs': '1;2;3', 
    #                   'score': '0',
    #                   'answer': 22.3,
    #                   'guess_string': '-22.3*cos(pi)',
    #                   'guess': 15.7,
    #                   'type': 'D',
    #                 },
    #           '2': {
    #                   'pk: '52'
    #                   'inputs': '8;-2', 
    #                   'score': '1',
    #                   'answer': 3.226,
    #                   'guess': '3.226',
    #                   'guess_string': '3.226',
    #                   'type': 'MC',
    #                   'mc_choices': ['3.226', '14', '23', '5.22'],
    #                 },
    #          }
    #          Indicates that the first question is a MarkedQuestion with pk=13, the inputs to
    #          this question were v=[1,2,3], and the student got the question wrong with a guess of 15.7
    result  = models.TextField(default='{}')
    score   = models.IntegerField(null=True)
    _q_order = models.TextField(default='')

    class Meta:
        verbose_name = "Quiz Result"

    @property
    def q_order(self):
        return json.loads(self._q_order)

    @q_order.setter
    def q_order(self, value):
        """ Value should be a list of integers """
        self._q_order = json.dumps(value)
        self.save()

    def update_score(self):
        """ Adds one to the overall score """
        self.score += 1
        self.save()

    def update_result(self, result):
        """ Takes a python dictionary, serializes it, and stores it in the result column.
            Input: result (dict) - the python dictionary.
            Output: Void
        """
        self.result = json.dumps(result)
        self.save()

    def get_result(self):
        """ Returns a python dictionary with the student quiz results
            Input: None
            Output: result (dict) - The python dictionay of results
                    attempt (string) - The current attempt, as a string to access in result
        """
        result = json.loads(self.result)
        attempt = str(self.cur_quest)
        return result, attempt

    def add_question_number(self):
        """ Adds one to the cur_quest field. However, checks if we have surpassed the last question,
            and if so sets cur_quest to 0.
            Input: None
            Output: is_last (Boolean) - indicated whether the cur_quest field has been set to 0
            TODO: Change this to allow for non-sequential numbering of
                  categories
        """
        num_quests = self.quiz.out_of
        if self.cur_quest == num_quests:
            is_last = True
            self.cur_quest = 0
        else:
            is_last = False
            self.cur_quest += 1
        self.save()
        
        return is_last

    @classmethod
    def create_new_record(cls, student, quiz, attempt=1):
        """ Creates a new StudentQuizResult record, instantiating a lot of
            redundant information.
            <<INPUT>>
            student (User) 
            quiz (Quiz)
            attempt (Integer default 1) The attempt number
        """
        # Create _q_order by randomizing the sequence [0,1,2,...,quiz.out_of-1]
        order = [x for x in range(0,quiz.out_of)]
        random.shuffle(order)
        order = json.dumps(order)
        new_record = cls(
            student=student, quiz=quiz, attempt=attempt,
            score=0, result='{}', cur_quest=1,
            _q_order = order
        )
        new_record.save()
        return new_record

 
    def __str__(self):
        return self.student.username + " - " + self.quiz.name + " - Attempt: " + str(self.attempt)

# --- Quizzes (end) --- #

class Typo(models.Model):
    user = models.ForeignKey(User, null=True)

    DOC_CHOICES = getattr(settings, 'DOC_CHOICES')
    document = models.CharField(max_length=100, choices=DOC_CHOICES)

    page = models.IntegerField()
    description = models.TextField()

    verified = models.BooleanField(default = False)

    def set_user(self, user):
        self.user = user
        self.save()

    def __str__(self):
        return 'Document: ' + self.document + ', Page: ' + str(self.page)

    def verify(self):
        self.verified = True
        self.save()

class StudentMark(models.Model):
    user     = models.ForeignKey(User, related_name='marks')
    category = models.ForeignKey(Evaluation)
    score    = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['user__username', 'category']

    def set_score(self, score, method=''):
        """ Method to set the score. Allows input of method which determines how to set the score.
            Input: score (float) - the value to update
                   method (String) - 'HIGH' only update the score if the input score is higher
              Out: old_score (float)  - the old score, for logging purposes
        """

        old_score = self.score

        if method == 'HIGH':
            self.score = max(self.score or 0, score)
        else:
            self.score = score

        self.save()

        return old_score

    def has_note(self):
        """ Checks if a StudentDocument (sicknote) has been submitted for this.
            Returns the StudentDocuments if so, and an empty array otherwise.
        """
        return StudentDocument.objects.filter(
                    user=self.user,
                    evaluation=self.category)

    def __str__(self):
        return "{user}: {score} in {category}".format(user=self.user, category=self.category.name, score=str(self.score)) 

class Tutorial(models.Model):
    """ For storing tutorial information.
    """
    name      = models.CharField(max_length=20)
    max_enrol = models.IntegerField()
    cur_enrol = models.IntegerField()
    ta        = models.ForeignKey(User, null=True, blank=True)
    add_info  = models.TextField(null=True,blank=True)

    def update_enrollment(self):
        self.cur_enrol=self.students.count()
        self.save()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return "Tutorial {tname}. Cur Enrol: {cur} of {max}".format(
                    tname=self.name, cur = self.cur_enrol, max=self.max_enrol)


class StudentInfo(models.Model):
    """ A model for storing student specific information. Initialized on registration and otherwise
        should be immutable.
    """
    user           = models.OneToOneField(User,related_name='info')
    student_number = models.CharField(max_length=20)
    tutorial       = models.ForeignKey(
                        Tutorial, 
                        null=True,
                        related_name='students')
    lecture        = models.CharField(max_length=20, null=True)

    def update(self, student_number, tutorial, lecture):
        self.student_number = student_number
        self.tutorial = tutorial
        self.lecture = lecture
        self.save()

    def change_tutorial(self, new_tutorial):
        """ Changes the student's tutorial. 
            new_tutorial (Tutorial model)
        """
        old_tutorial = self.tutorial

        # update the tutorial
        self.tutorial = new_tutorial
        self.save()

        # change enrollments
        new_tutorial.update_enrollment()
        if old_tutorial:
            old_tutorial.update_enrollment()

    class Meta:
        ordering = ['user', 'student_number', 'lecture', 'tutorial']

    def __str__(self):
        tut_info = self.tutorial.name if self.tutorial else "Unset"

        return "({un}) {fn} {ln} - {sn}: Lecture {l}, Tutorial {t}".format(
                   un = self.user.username,
                   fn = self.user.first_name,
                   ln = self.user.last_name,
                   sn = self.student_number,
                   t  = tut_info,
                   l  = self.lecture)
