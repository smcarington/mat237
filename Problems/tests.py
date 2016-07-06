from django.test import TestCase, LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from Problems.models import *
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AnnouncementTest(StaticLiveServerTestCase):
    fixtures = ['user.json', 'Problems.json', ]

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(6)

        #Change the announcements so that one is old and one is new
        old_ann = Announcement.objects.get(title='New announcement')
        old_ann.expires = timezone.now() + timezone.timedelta(days=1)
        old_ann.save()

        new_ann = Announcement.objects.get(title='Old Announcement')
        new_ann.expires = timezone.now() - timezone.timedelta(days=1)
        new_ann.save()

    def tearDown(self):
        self.browser.quit()

    def test_announcement_page(self):
        self.browser.get(self.live_server_url)
        body = self.browser.find_element_by_tag_name('body')

        # Check to see if the new announcement appears, and the old announcement
        # does not
        self.assertIn('New announcement', body.text)
        self.assertNotIn('Old Announcement', body.text)

        # Retrieve the old announcement and check that they appear
        self.browser.find_element_by_id('get_old').click()
        body = WebDriverWait(self.browser, 1000).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".old-ann>div")))
        self.assertIn('Old Announcement', body.text)

# Create your tests here.
