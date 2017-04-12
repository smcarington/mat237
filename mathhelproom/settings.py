from django.conf import settings

DAYS_OF_WEEk = getattr(settings, "MATHHELPROOM_DAYS_OF_WEEK",
                            [('Sun', 'Sunday'),
                             ('Mon', 'Monday'),
                             ('Tue', 'Tuesday'),
                             ('Wed', 'Wednesday'),
                             ('Thu', 'Thursday'),
                             ('Fri', 'Friday'),
                             ('Sat', 'Saturday')])

