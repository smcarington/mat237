from django.test import TestCase, LiveServerTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from Problems.models import *
from selenium import webdriver
from selenium.webdriver.common.key import Keys

class AnnouncementTest(LiveServerTestCase):
    fixtures = ['user.json', 'Problems.json', ]

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(6)

        #Change the announcements so that one is old and one is new
        old_ann = Announcement.objects.get(title='New announcement')
        old_ann.expires = timezone.now() + timezone.timedelta(days=1)

        new_ann = Announcement.objects.get(title='Old Announcement')
        new_ann.expires = timezone.now() - timezone.timedelta(days=1)

    def tearDown(self):
        self.browser.quit()

    def test_announcement_page(self):
        self.browser.get(self.live_server_url)
        self.browser.find_element_by_tag('body')

# Create your tests here.
