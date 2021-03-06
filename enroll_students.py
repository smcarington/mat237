from django.core.mail import send_mail
from django.contrib.auth.models import User

# Import the students into a multi-dimensional array

with open('email_list_test.txt') as e_file:
    lines = [line.split() for line in e_file]

# You may want to first check that the array is formatted correctly
#
# for i,item in enumerate(lines):
#   if len(item) > 2:
#       print(i)
#
# which will tell you which lines need to be manually fixed. Should
# return empty if properly formatted. Otherwise, use lines[i].remove('string')
# to remove that element from the array.

subject_line = "MAT237 Website and Login Credentials"
body         =
""" Welcome to MAT237. The course website is located at

    http://www.mat237.math.toronto.edu

    where your username is {username} and password is {password}. When you login, you will be able to change your password.

    All the best,
    The MAT237 Instructors
"""

for user in lines:
    [user_name, email] = user
    
    # Create user instance in database with randomly generated password. Email
    # this password to the user
    user  = User(username=user_name, email=email)
    rpass = User.objects.make_random_password()
    user.set_password(rpass)

    custom_message = body.format(username=user_name, password=rpass)

    send_mail(subject, custom_message, "tholden@math.toronto.edu", [email])

    print('Email sent to {username}'.format(username=user_name))
