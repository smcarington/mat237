from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.test.utils import setup_test_environment
from django.utils import timezone
from .models import *

# Create your tests here.

class ModelTests(TestCase):
    """ Test suite for the mathhelproom models """

    def setUp(self):
        """ Create an admin and two TA users """
        User.objects.create(username="admin", email="admin@...", password="admin")
        User.objects.create(username="TA-John", email="john@...",
                password="johns_passowrd")
        User.objects.create(username="TA-Michelle", email="michell@...",
                password="michelles_password")

    def test_add_UserInfo(self):
        """ Tests: mathhelproom.models.UserInfo 
            Add info to the Admin and the TAs 
        """

        admin = User.objects.get(username="admin")
        UserInfo.objects.create(user=admin,
                                course="MAT134",
                                is_ta=False, is_admin = True,
                                num_blocks=0,
                                phone="555-555-5555")

        john = User.objects.get(username="TA-John")
        UserInfo.objects.create(user=john,
                                course="MAT133",
                                is_ta=True, is_admin = False,
                                num_blocks=3,
                                phone="000-000-0000")

        michelle = User.objects.get(username="TA-Michelle")
        UserInfo.objects.create(user=michelle,
                                course="MAT135",
                                is_ta=True, is_admin = False,
                                num_blocks=4,
                                phone="999-999-9999")

        self.assertEqual(john.mhr_info.phone, "000-000-0000")
        self.assertIs(john.mhr_info.is_admin, False)
        self.assertIs(admin.mhr_info.is_admin, True)
