import os
import sys

sys.path.append('/var/lib/django')
sys.path.append('/var/lib/django/iavq')

os.environ['DJANGO_SETTINGS_MODULE'] = 'iavq.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

