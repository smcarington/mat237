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

        # Generate sorting code as follows: 
        # 023_M15_0102-12 = 23 student globally, 15th student with M last name, 
        # Tutorial 0102, 12th in that tutorial alphabetically
       
        glob_count    = 0
        tutorial_list = StudentInfo.objects.values('tutorial').distinct()
        tut_dict      = {tut_name: 0 for tut_name in tutorial_list}
        cur_letter    = 'A'
        let_number    = 0

        # Get current number of students in class, to use for number padding
        padding = len(str(students.count()))
        template = "{glob:0>{pad}d}_{let}{let_num}_{tutorial}-{tut_num}}"

        for student in students:
            try:
                stud_tutorial  = student.info.tutorial
                stud_last_name = student.last_name

                global_count   += 1
                tutorial[stud_tutorial] += 1

                #Check to see if last name letter has changed
                if stud_last_name[0] == cur_letter:
                    let_number += 1
                else:
                    cur_letter = stud_last_name[0]
                    let_number = 1

                sort_string = template.format(
                                glob = global_count,
                                pad  = padding,
                                let  = cur_letter,
                                let_num = let_number,
                                tutorial = stud_tutorial,
                                tut_num = tut_dict[stud_tutorial])

                print(json.dumps({'first_name': student.first_name,
                                  'last_name' : student.last_name,
                                  'student_number': student.info.student_number,
                                  'tutorial': student.info.tutorial,
                                  'sort': sort_string})
                     )
            
            except Exception as e:
                string = 'ERROR: User {} {} with username {} \n Exception: {e}'.format(student.first_name, student.last_name, student.username,e=e)
                logging.error(string)
