"""
WSGI config for Mat237 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os, time, traceback, signal, sys
from django.core.wsgi import get_wsgi_application

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Mat237.settings")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    application = get_wsgi_application()
    print('WSGI without exception')
except Exception:
    print('handling WSGI exception')
    if 'mod_wsgi' in sys.modules:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(2.5)


#application = get_wsgi_application()
