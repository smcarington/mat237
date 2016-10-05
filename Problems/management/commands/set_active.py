from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
from django.db import IntegrityError

import logging

class Command(BaseCommand):
    """ A command for updating whether students are active. Expects a comma 
        separated list, where the username is the first object, and the rest are ignored
        If the name is not in the list, the student will be made inactive.
    """

    def add_arguments(self, parser):
        parser.add_argument('filename')
        parser.add_argument('--log', dest='log')

    def handle(self, *args, **options):
        if options['log']:
            logging.basicConfig(filename=options['log'], level=logging.DEBUG)

        with open(options['filename']) as e_file:
            lines = [line.strip().split(',') for line in e_file]

        # Marks all students as inactive
        User.objects.filter(is_staff=False).update(is_active=False)
        # Get the list of usernames
        usernames = [row[0].strip() for row in lines]

        try:
            active_users = User.objects.filter(username__in=usernames)
            active_users.update(is_active=True)

            # Print the list of inactive students
            not_active_students = User.objects.filter(is_active=False)

            if not_active_students:
                for user in not_active_students:
                    print("{} {} is no longer active.".format(user.first_name, user.last_name))

            print("\n   Active user count: {}\n   Non-active user count: {} ".format(active_users.count(), not_active_students.count()))

        except Exception as e:
            string = 'ERROR: \n Exception: {e}'.format(e=e)
            print(string)
            logging.error(string)
