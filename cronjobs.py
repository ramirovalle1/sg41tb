#!/usr/bin/env python

import sys,os

# Full path and name to your csv file


SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

csv_filepathname= "arreglo.csv"
# Full path to your django project directory
your_djangoproject_home=os.path.split(SITE_ROOT)[0]

sys.path.append(your_djangoproject_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


from settings import DEFAULT_PASSWORD, ALUMNOS_GROUP_ID, SEXO_MASCULINO, SEXO_FEMENINO
#from sga.models import *
from datetime import datetime
from sga.models import LeccionGrupo

# Cerrar clases abiertas despues de clases

leccionesGrupos = LeccionGrupo.objects.filter(abierta=True)

ahora = datetime.now().time()

print("1 - Cerrando Clases Abiertas despues de Tiempo")
for lg in leccionesGrupos:

    if lg.turno.termina < ahora and lg.contenido!=None and lg.contenido.strip()!="":
        print("Leccion: "+str(lg),)
        lg.abierta = False
        lg.horasalida = ahora
        lg.save()
        for leccion in lg.lecciones.all():
            print(leccion)
            leccion.abierta = False
            leccion.horasalida = ahora
            leccion.save()
        print(" CERRADA")
print("HECHO")