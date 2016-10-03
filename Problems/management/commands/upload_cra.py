from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError

from Problems.models import StudentMark, ExemptionType

import logging

class Command(BaseCommand):
    """ A command for taking CRA data and updating student grades
        Expects a comma separated list
        username, email, student_number, first_name, last_name, cra_score
    """

    def add_arguments(self, parser):
        parser.add_argument('filename')
        parser.add_argument('--log', dest='log')

    def handle(self, *args, **options):
        if options['log']:
            logging.basicConfig(filename=options['log'], level=logging.DEBUG)

        exemption, created = ExemptionType.objects.get_or_create(name="CRA", out_of="100")

        with open(options['filename']) as e_file:
            lines = [line.strip().split(',') for line in e_file]

        for user in lines:
            try:
                [username, email, student_number, first_name, last_name, cra_score] = [item.strip() for item in user]
                
                user = User.objects.get(username=username, 
                                        first_name=first_name,
                                        last_name=last_name)
              
                print('Updating CRA score for {} {}. Score {}'.format(user.first_name, user.last_name, cra_score))

                if not cra_score:
                    cra_score = 0

                stud_mark, created = StudentMark.objects.get_or_create(user=user, category=exemption)
                stud_mark.set_score(round(float(cra_score)))
            except Exception as e:
                string = 'ERROR: {first} {last} with username: {username} at {email}. \n Exception: {e}'.format(first=first_name, last=last_name, username=username, email=email, e=e)
                print(string)
                logging.error(string)
