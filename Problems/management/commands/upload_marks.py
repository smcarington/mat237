from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError

from Problems.models import StudentMark, ExemptionType

import logging

class Command(BaseCommand):
    """ A command for uploading marks. Expects a comma separated list
        username, student_number, first_name, last_name, score
    """

    def add_arguments(self, parser):
        parser.add_argument('category')
        parser.add_argument('filename')
        parser.add_argument('--log', dest='log')

    def handle(self, *args, **options):
        if options['log']:
            logging.basicConfig(filename=options['log'], level=logging.DEBUG)

        exemption, created = ExemptionType.objects.get_or_create(name=options['category'])

        with open(options['filename']) as e_file:
            lines = [line.strip().split(',') for line in e_file]

        for user in lines:
            try:
                [username, student_number, first_name, last_name, score] = [item.strip() for item in user]
                
                user = User.objects.get(username=username, 
                                        first_name=first_name,
                                        last_name=last_name)
              
                print('Updating {} score for {} {}. Score {}'.format(exemption.name, user.first_name, user.last_name, score))

                if not score:
                    score = 0

                stud_mark, created = StudentMark.objects.get_or_create(user=user, category=exemption)
                stud_mark.set_score(round(float(score)))
            except Exception as e:
                string = 'ERROR: {first} {last} with username: {username}. \n Exception: {e}'.format(first=first_name, last=last_name, username=username, e=e)
                print(string)
                logging.error(string)
