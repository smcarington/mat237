from django.test import TestCase, LiveServerTestCase, Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import Client
from django.core.urlresolvers import reverse

from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Problems.models import *

#class AnnouncementTest(StaticLiveServerTestCase):
#    fixtures = ['user.json', 'Problems.json', ]
#
#    def setUp(self):
#        self.browser = webdriver.Firefox()
#        self.browser.implicitly_wait(6)
#
#        #Change the announcements so that one is old and one is new
#        old_ann = Announcement.objects.get(title='New announcement')
#        old_ann.expires = timezone.now() + timezone.timedelta(days=1)
#        old_ann.save()
#
#        new_ann = Announcement.objects.get(title='Old Announcement')
#        new_ann.expires = timezone.now() - timezone.timedelta(days=1)
#        new_ann.save()
#
#    def tearDown(self):
#        self.browser.quit()
#
#    def test_announcement_page(self):
#        self.browser.get(self.live_server_url)
#        body = self.browser.find_element_by_tag_name('body')
#
#        # Check to see if the new announcement appears, and the old announcement
#        # does not
#        self.assertIn('New announcement', body.text)
#        self.assertNotIn('Old Announcement', body.text)
#
#        # Retrieve the old announcement and check that they appear
#        self.browser.find_element_by_id('get_old').click()
#        body = WebDriverWait(self.browser, 1000).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".old-ann>div")))
#        self.assertIn('Old Announcement', body.text)

class QuizParserTest(TestCase):
    fixtures = ['user.json', 'Quiz.json']
    logged_in = False

    def setUp(self):
        self.client = Client()
        self.username = 'superuser'
        self.password = 'djangosuperuser'
        self.is_staff = True
        self.user = User.objects.create_user(username=self.username, password=self.password, is_staff= self.is_staff)

        self.logged_in = self.client.login(username=self.username, password=self.password)
        self.assertTrue(self.logged_in)

    def test_parse_abstract_choice(self):
        import Problems.views
        choice = "14; rand(0,100); uni(0,1,2)"
        output = Problems.views.parse_abstract_choice(choice)
        self.assertEqual(len(output.split(';')),3)

    def test_quiz_page(self):
        self.assertTrue(self.logged_in)
        response = self.client.get(reverse('quizzes'))
        # Make sure the quizzes appear
        self.assertIn('Quiz 1', str(response.content))
        self.assertIn('Quiz 2', str(response.content))
        self.assertIsInstance(response.context['all_quizzes'][0], Quiz)

    def test_edit_mquestion(self):
        """ Tests the creation and editing of a quiz and questions in that quiz.
        """
        self.assertTrue(self.client.login(username='superuser', password='djangosuperuser'))

        # First create a new quiz
        response = self.client.post(reverse('new_quiz'), 
                {'name': 'New Quiz', 
                 'tries': 0, 
                 'live': (timezone.now() - timezone.timedelta(days=1)).strftime("%Y-%m-%d %I:%M"),
                 'expires': (timezone.now() + timezone.timedelta(days=1)).strftime("%Y-%m-%d %I:%M"),
                }, follow=True)
        latest_quiz = Quiz.objects.latest('pk')
        self.assertEqual(latest_quiz.name, "New Quiz")

        # Add a marked question to that quiz
        problem_statement="What is one more that {v[0]}?"
        response = self.client.post(reverse('edit_quiz_question', args=(latest_quiz.pk,)), 
                {'category': '1', 
                 'problem_str': problem_statement, 
                 'answer': "{v[0]}+1",
                 'q_type': "D",
                 'functions': "{}",
                 'mc_choices': "[]",
                }, follow=True)
        
        # Check to see that this submitted correctly
        mquestion = MarkedQuestion.objects.latest('pk')
        # Number of variables is set by a model method. Verify it worked correctly
        num_vars = mquestion.num_vars
        self.assertEqual(num_vars,1)

        self.assertEqual(mquestion.problem_str, problem_statement)

        # Should be on the choices editing page, so let's submit some choices
        self.assertIn('Add and Edit Choices', str(response.content))
        response = self.client.post(reverse('edit_choices', args=(mquestion.pk,)),
                {'new_choice': "rand(0,100)",
                })
        self.assertIn("\mathbb Z", str(response.content))

        # Edit that quiz
        response = self.client.post(reverse('edit_quiz', args=(latest_quiz.pk,)),
                {'name': 'Edited Quiz', 
                 'tries': 2, 
                 'live': (timezone.now() - timezone.timedelta(days=2)).strftime("%Y-%m-%d %I:%M"),
                 'expires': (timezone.now() + timezone.timedelta(days=2)).strftime("%Y-%m-%d %I:%M"),
                }, follow=True)
                
        latest_quiz = Quiz.objects.latest('pk')
        self.assertEqual(len(Quiz.objects.filter(name="New Quiz")), 0)

        # Now edit the marked question, only by changing the number of variables
        new_problem_statement = "How many roots does \( {v[1]}cos({v[0]}x) \) have in [0,1]?"
        response = self.client.post(reverse('edit_quiz_question', kwargs={'quizpk':latest_quiz.pk, 'mpk': mquestion.pk, }), 
                {'category': '1', 
                 'problem_str': new_problem_statement, 
                 'answer': "floor({v[0]}/(2*pi))*gobble({v[1]})",
                 'q_type': "D",
                 'functions': "{'floor': lambda x: math.floor(x)}",
                 'mc_choices': "[]",
                }, follow=True)

        mquestion = MarkedQuestion.objects.latest('pk')
        self.assertEqual(len(MarkedQuestion.objects.filter(problem_str = problem_statement)),0)
        self.assertEqual(mquestion.num_vars,2)

        # Delete the old choice for this mquestion and give a new option.
        # Note that deleting the old choice depends on AJAX, so we cannot do it through client. 
        # Instead, we will just edit the old one. But first we check error handling on choice
        response = self.client.post(reverse('edit_choices', args=(mquestion.pk,)),
                {'new_choice': "rand(0,100)",
                })
        self.assertIn("Incorrect number of variables", str(response.content))

        response = self.client.post(reverse('edit_choices', args=(mquestion.pk,)),
                {'new_choice': '',
                 'old_choice': "10;rand(0,100)",
                })

        # Check to see if we get the correct answer when we attempt to write this quiz
        response = self.client.get(reverse('start_quiz', kwargs={'quizpk': latest_quiz.pk}))
        # This should have created a StudentQuizResult
        self.assertEqual(StudentQuizResult.objects.filter(student=self.user).count(),1)
        sqr = StudentQuizResult.objects.latest('pk')

        # Make sure the question renders:
        response = self.client.get(reverse('display_question', kwargs={"sqrpk": sqr.pk}))
        # Post an answer
        response = self.client.post(reverse('display_question', 
            kwargs={"sqrpk": sqr.pk, 
                    'submit': 'submit'}),
            {'problem': '', # Shouldn't be empty, but also shouldn't matter
             'answer': 'sin(pi/2)', # Double check that functions work
             }
            )

        self.assertIn('paleblue', str(response.content)) #paleblue is the class of the results table

        # Refresh the sqr
        sqr.refresh_from_db()
        self.assertEqual(sqr.score, 1)


        # Enter the question and submit the correct answer



# Create your tests here.
#
# Quiz Tests:
# 0. Test quiz question validation for random ranges
# 1. Test student answer input validation
# 2. display_question/submit when already last question (ie referesh at terminal page)
# 3. Students not allowed to vote more times that allowed
# 4. Students leaving a quiz then resuming
