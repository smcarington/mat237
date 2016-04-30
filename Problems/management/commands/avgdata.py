from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from Problems.models import QuestionStatus, Question

# A command which updates the attempted, solved, difficulty averages.
# All data should be an integer. For attempted/solved it should be a
# percent, like 15 -> 15%, and for difficulty a digit in {1,...,10}
class Command(BaseCommand):
    
    def handle(self, *args, **kwargs):
        total_users   = User.objects.all().count()
        question_list = Question.objects.all();

        for question in question_list:
            qstatus   = question.status
            att_list  = qstatus.values_list('attempt', flat=True)
            sol_list  = qstatus.values_list('solved', flat=True)
            diff_list = qstatus.values_list('difficulty', flat=True)

            #Compute total attempt percentage
            question.attempts  = round(100*float(sum(att_list))/total_users)
            question.solved    = round(100*float(sum(sol_list))/total_users)
            question.stud_diff = round(sum(diff_list)/float(len(diff_list)))

            self.stdout.write("Updated info for Question: {question}. New values are A:{att}, S:{sol}, D:{dif}".format(question=question, att=question.attempts, sol = question.solved, dif=question.stud_diff))

            question.save()
