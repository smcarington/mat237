from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError

from Problems.models import *

class Command(BaseCommand):
    """ A command for registering student en masse.
        Expects a comma separated list
        lecture, tutorial, student_number, last_name, first_name, email, username
    """

    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, *args, **options):
        with open(options['filename']) as e_file:
            lines = [line.strip().split(',') for line in e_file]

        # You may want to first check that the array is formatted correctly
        #
        # for i,item in enumerate(lines):
        #   if len(item) > 2:
        #       print(i)
        #
        # which will tell you which lines need to be manually fixed. Should
        # return empty if properly formatted. Otherwise, use lines[i].remove('string')
        # to remove that element from the array.

        subject_line = "{site_name} Website and Login Credentials".format(site_name=settings.SITE_NAME)
        body         = """Welcome to {site_name}. The course website is located at

{site_url}

where your username is {username} and password is {password}. It is recommended that you login and change your password immediately. 

All the best,
The {site_name} Instructors"""

        for user in lines:
            try:
#                [first, last, user_name, email] = user
                [lecture, tutorial, student_number, last_name, first_name, email, username] = [item.strip() for item in user]
                
                # Create user instance in database with randomly generated password. Email
                # this password to the user
                
                user, created = User.objects.get_or_create(username=username, 
                                                     first_name=first_name,
                                                     last_name=last_name)
                # Email could change between updates
                user.email = email
                user.save()

                if not created:
                    tutorial = Tutorial.objects.get(name=tutorial)
                    print('User {} {} already exists. Updating information'.format(first_name, last_name))
                    try: # If somehow the info does not exist, we make it
                        user.info.update(student_number = student_number,
                                     tutorial = tutorial,
                                     lecture = lecture)
                    except StudentInfo.DoesNotExist as e:
                        user_info = StudentInfo(user = user,
                                        student_number = student_number,
                                        tutorial = tutorial,
                                        lecture = lecture)
                        user_info.save()
                else:
                    print('Creating user for {} {}.'.format(first_name, last_name))
                    rpass = User.objects.make_random_password()
                    user.set_password(rpass)
                    user.save()

                    # Now create the additional user information model
                    user_info = StudentInfo(user = user,
                                            student_number = student_number,
                                            tutorial = tutorial,
                                            lecture = lecture)
                    user_info.save()

                    # Now send the email
                    custom_message = body.format(username = username, 
                                                 password = rpass, 
                                                 site_name= settings.SITE_NAME,
                                                 site_url = settings.SITE_URL)

                    send_mail(subject_line, custom_message, "tholden@math.toronto.edu", [email])

                    print('Email sent to {first} {last} with username: {username} at {email}'.format(first=first_name, last=last_name,username=username, email=email))
            except Exception as e:
                print(e)
                print('ERROR: {first} {last} with username: {username} at {email}. \n Exception: {e}'.format(first=first_name, last=last_name, username=username, email=email, e=e))
