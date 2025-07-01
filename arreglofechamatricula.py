#!/usr/bin/env python

import sys,os

# Full path and name to your csv file
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from sga.models import *
from django.contrib.admin.models import LogEntry

CONTENT_TYPE_MATRICULA = 55

for m in Matricula.objects.all().order_by('id'):
    if LogEntry.objects.filter(object_id=m.id, content_type__id=CONTENT_TYPE_MATRICULA).exists():
        l = LogEntry.objects.filter(object_id=m.id, content_type__id=CONTENT_TYPE_MATRICULA)[:1].get()
        m.fecha = l.action_time.date()
        m.save()
    else:
        m.fecha = m.nivel.inicio
        m.save()

    print(str(m.id) + ' -> ' + m.fecha.strftime('%d-%m-%Y'))




