from django.contrib.auth.backends import RemoteUserBackend

class CourseSpecificBackend(RemoteUserBackend):
    create_unknown_user = False
