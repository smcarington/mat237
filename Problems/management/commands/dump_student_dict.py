from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

import logging, json
from Problems.models import StudentInfo

class Command(BaseCommand):
    """ Dumps the student information as a JSON objects to a text file.
    """

    def add_arguments(self, parser):
        parser.add_argument('--log', 
                            dest='log',
                            help="Location of the logfile")
        parser.add_argument('--all', 
                            action='store_true',
                            dest='all',
                            default=False,
                            help="Print all students, not just active students. Default = False")

    def handle(self, *args, **options):
        if options['log']:
            logging.basicConfig(filename=options['log'], level=logging.DEBUG)

        # Marks all students as inactive
        students=User.objects.filter(is_staff=False, is_active=not options['all']).prefetch_related('info').order_by('last_name')

        for student in students:
            try:
                print(json.dumps({'first_name': student.first_name,
                                  'last_name' : student.last_name,
                                  'student_number': student.info.student_number,
                                  'tutorial': student.info.tutorial})
                     )
            
            except Exception as e:
                string = 'ERROR: User {} {} with username {} \n Exception: {e}'.format(student.first_name, student.last_name, student.username,e=e)
                logging.error(string)
