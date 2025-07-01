#!/usr/bin/env python

import sys,os

# Full path and name to your csv file

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from sga.models import Inscripcion

# Actualizar el modelo Inscripcion Estadisticas para las deudas, creditos, edades y estados de matriculacion de los alumnos

inscripciones = Inscripcion.objects.all()

print("ACTUALIZAR ESTADISTICAS DE TODAS LAS INSCRIPCIONES")

for i in inscripciones:
    i.actualiza_estadistica()
print("HECHO")