from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError

from Problems.models import StudentMark, Evaluation

import logging

class Command(BaseCommand):
    """ A command for uploading marks. Expects a comma separated list
        student_number, score
    """

    def add_arguments(self, parser):
        parser.add_argument('category')
        parser.add_argument('filename')
        parser.add_argument('--log', dest='log')

    def handle(self, *args, **options):
        if options['log']:
            logging.basicConfig(filename=options['log'], level=logging.DEBUG)

        exemption, created = Evaluation.objects.get_or_create(name=options['category'])

        with open(options['filename']) as e_file:
            lines = [line.strip().split(',') for line in e_file]

        for user in lines:
            try:
                [student_number, score] = [item.strip() for item in user]
                
                try:
                    user = User.objects.get(info__student_number=student_number)
                except Exception as e:
                    string = 'Error! {}'.format(e)
                    print(string)
                    logging.error(string)
                    continue
              
                print('Updating {} score for {} {}. Score {}'.format(exemption.name, user.first_name, user.last_name, score))

                if not score:
                    score = 0

                stud_mark, created = StudentMark.objects.get_or_create(user=user, category=exemption)
                stud_mark.set_score(round(float(score)))
            except Exception as e:
                string = 'ERROR: {first} {last} with username: {username}. \n Exception: {e}'.format(first=first_name, last=last_name, username=username, e=e)
                print(string)
                logging.error(string)
