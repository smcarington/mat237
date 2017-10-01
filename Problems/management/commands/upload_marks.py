from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError

<<<<<<< HEAD
from Problems.models import StudentMark, Evaluation
=======
from Problems.models import StudentMark, ExemptionType
>>>>>>> fead8ced507f999bce693098ef96a753b7c9a7ff

import logging

class Command(BaseCommand):
    """ A command for uploading marks. Expects a comma separated list
<<<<<<< HEAD
        student_number, score
=======
        username, student_number, first_name, last_name, score
>>>>>>> fead8ced507f999bce693098ef96a753b7c9a7ff
    """

    def add_arguments(self, parser):
        parser.add_argument('category')
        parser.add_argument('filename')
        parser.add_argument('--log', dest='log')

    def handle(self, *args, **options):
        if options['log']:
            logging.basicConfig(filename=options['log'], level=logging.DEBUG)

<<<<<<< HEAD
        exemption, created = Evaluation.objects.get_or_create(name=options['category'])
=======
        exemption, created = ExemptionType.objects.get_or_create(name=options['category'])
>>>>>>> fead8ced507f999bce693098ef96a753b7c9a7ff

        with open(options['filename']) as e_file:
            lines = [line.strip().split(',') for line in e_file]

        for user in lines:
            try:
<<<<<<< HEAD
                [student_number, score] = [item.strip() for item in user]
                
                try:
                    user = User.objects.get(info__student_number=student_number)
                except Exception as e:
                    string = 'Error! {}'.format(e)
                    print(string)
                    logging.error(string)
                    continue
=======
                [username, student_number, first_name, last_name, score] = [item.strip() for item in user]
                
                user = User.objects.get(username=username, 
                                        first_name=first_name,
                                        last_name=last_name)
>>>>>>> fead8ced507f999bce693098ef96a753b7c9a7ff
              
                print('Updating {} score for {} {}. Score {}'.format(exemption.name, user.first_name, user.last_name, score))

                if not score:
                    score = 0

                stud_mark, created = StudentMark.objects.get_or_create(user=user, category=exemption)
                stud_mark.set_score(round(float(score)))
            except Exception as e:
                string = 'ERROR: {first} {last} with username: {username}. \n Exception: {e}'.format(first=first_name, last=last_name, username=username, e=e)
                print(string)
                logging.error(string)
